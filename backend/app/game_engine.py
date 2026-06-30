import random
import asyncio
from typing import List, Tuple, Optional, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from .models import Game, Player, User, GameStatus, Cartela
from .redis_client import redis_client
from .config import get_settings

settings = get_settings()

class BingoGameEngine:
    """Core bingo game logic with support for all standard patterns"""
    
    @staticmethod
    def generate_bingo_card() -> List[List[int]]:
        """
        Generate a standard 75-ball bingo card with numbers 1-75
        Returns: List of 5 columns, each containing 5 numbers
        Card structure: card[col][row] where col=0-4 (B,I,N,G,O) and row=0-4
        
        Column ranges:
        - B (col 0): 1-15
        - I (col 1): 16-30
        - N (col 2): 31-45 (center is FREE = 0)
        - G (col 3): 46-60
        - O (col 4): 61-75
        """
        card = []
        ranges = [
            (1, 15),    # B column
            (16, 30),   # I column
            (31, 45),   # N column
            (46, 60),   # G column
            (61, 75)    # O column
        ]
        
        for col_idx, (start, end) in enumerate(ranges):
            # Select 5 unique random numbers from this column's range
            column = random.sample(range(start, end + 1), 5)
            
            # Set center cell (N column, middle row) as FREE
            if col_idx == 2:  # N column
                column[2] = 0  # Middle position (row 2) is FREE
            
            card.append(column)
        
        return card
    
    @staticmethod
    def validate_bingo_card(card: List[List[int]]) -> bool:
        """
        Validate that a bingo card follows standard 75-ball rules
        Returns True if valid, False otherwise
        """
        if len(card) != 5:
            return False
        
        ranges = [
            (1, 15),    # B
            (16, 30),   # I
            (31, 45),   # N
            (46, 60),   # G
            (61, 75)    # O
        ]
        
        all_numbers = set()
        
        for col_idx, column in enumerate(card):
            if len(column) != 5:
                return False
            
            start, end = ranges[col_idx]
            
            for row_idx, num in enumerate(column):
                # Check FREE space
                if col_idx == 2 and row_idx == 2:
                    if num != 0:
                        return False
                    continue
                
                # Check number is in valid range for this column
                if not (start <= num <= end):
                    print(f"Invalid number {num} in column {col_idx} (expected {start}-{end})")
                    return False
                
                # Check for duplicates
                if num in all_numbers:
                    print(f"Duplicate number {num} found")
                    return False
                
                all_numbers.add(num)
        
        return True
    
    @staticmethod
    def get_number_category(number: int) -> str:
        """Get BINGO category for a number"""
        if 1 <= number <= 15:
            return "B"
        elif 16 <= number <= 30:
            return "I"
        elif 31 <= number <= 45:
            return "N"
        elif 46 <= number <= 60:
            return "G"
        elif 61 <= number <= 75:
            return "O"
        return ""
    
    @staticmethod
    def call_next_number(remaining_numbers: List[int]) -> Optional[int]:
        """
        Call next number using pop() method (like real Bingo).
        Numbers are pre-shuffled when game starts, then popped one by one.
        This GUARANTEES no duplicates - each number called exactly once.
        
        Args:
            remaining_numbers: Shuffled list of numbers not yet called
            
        Returns:
            Next number to call, or None if all numbers called
        """
        if not remaining_numbers:
            return None
        # Pop the last number (most efficient, O(1) operation)
        return remaining_numbers.pop()
    
    @staticmethod
    def mark_number(card: List[List[int]], marked: List[int], number: int) -> List[int]:
        """Mark a number on the card if it exists
        Card is stored as columns: card[col][row]
        But we need to mark using row-major indices for check_win
        """
        # Card is stored as 5 columns, each with 5 numbers
        # card[col][row] where col=0-4 (B,I,N,G,O) and row=0-4
        for col_idx in range(5):
            for row_idx in range(5):
                if card[col_idx][row_idx] == number:
                    # Convert to row-major flat index: row * 5 + col
                    flat_idx = row_idx * 5 + col_idx
                    if flat_idx not in marked:
                        marked.append(flat_idx)
        return marked
    
    @staticmethod
    def check_win(card: List[List[int]], marked: List[int]) -> Tuple[bool, Optional[str]]:
        """
        Check if the card has a winning pattern
        Supports: horizontal rows, vertical columns, diagonals, four-corner, blackout
        Returns: (has_won, pattern_type)
        
        Note: Blackout is checked first as it's the most valuable pattern
        """
        # Convert flat indices to 2D coordinates
        marked_coords = {(idx // 5, idx % 5) for idx in marked}
        
        # Center is always marked (FREE)
        marked_coords.add((2, 2))
        
        # Check blackout FIRST (all 25 cells marked) - most valuable pattern
        if len(marked_coords) >= 25:
            return True, "blackout"
        
        # Check four corners
        corners = [(0, 0), (0, 4), (4, 0), (4, 4)]
        if all(corner in marked_coords for corner in corners):
            return True, "four_corner"
        
        # Check rows (horizontal)
        for row in range(5):
            if all((row, col) in marked_coords for col in range(5)):
                return True, f"row_{row}"
        
        # Check columns (vertical)
        for col in range(5):
            if all((row, col) in marked_coords for row in range(5)):
                return True, f"col_{col}"
        
        # Check diagonal (top-left to bottom-right)
        if all((i, i) in marked_coords for i in range(5)):
            return True, "diagonal_lr"
        
        # Check diagonal (top-right to bottom-left)
        if all((i, 4 - i) in marked_coords for i in range(5)):
            return True, "diagonal_rl"
        
        return False, None


class GameManager:
    """Manages game lifecycle and state"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_game(self, room: str, entry_fee: float) -> Game:
        """Create a new game with pre-shuffled number deck"""
        import uuid
        game_id = f"GAME-{uuid.uuid4().hex[:8].upper()}"
        
        # Create shuffled deck of numbers 1-75 (like real Bingo)
        remaining_numbers = list(range(1, 76))
        random.shuffle(remaining_numbers)
        
        game = Game(
            game_id=game_id,
            room=room,
            entry_fee=entry_fee,
            status=GameStatus.WAITING,
            remaining_numbers=remaining_numbers  # Pre-shuffled deck
        )
        
        self.db.add(game)
        await self.db.commit()
        await self.db.refresh(game)
        
        # Initialize Redis state
        await redis_client.set_game_state(game_id, {
            "status": GameStatus.WAITING.value,
            "players": 0,
            "called_numbers": [],
            "current_number": None
        })
        
        await redis_client.init_remaining_numbers(game_id, remaining_numbers)
        await redis_client.add_active_game(game_id)
        
        print(f"Created game {game_id} with shuffled deck: {remaining_numbers[:10]}... (showing first 10)")
        
        return game
    
    async def get_cartela(self, cartela_number: int) -> Optional[Cartela]:
        """Get a permanent cartela by number"""
        result = await self.db.execute(
            select(Cartela).where(Cartela.cartela_number == cartela_number)
        )
        return result.scalar_one_or_none()
    
    async def join_game(self, game_id: str, user_id: int, card_number: int) -> Player:
        """Add player to game using permanent cartela"""
        # Check if card is available
        taken_by = await redis_client.get_card_status(game_id, card_number)
        if taken_by:
            raise ValueError(f"Card {card_number} is already taken")
        
        # Get game
        result = await self.db.execute(
            select(Game).where(Game.game_id == game_id)
        )
        game = result.scalar_one_or_none()
        if not game:
            raise ValueError("Game not found")
        
        # Only allow joining during WAITING and COUNTDOWN (standard Bingo rules)
        if game.status == GameStatus.FINISHED:
            raise ValueError("Game has already finished")
        
        if game.status == GameStatus.ACTIVE:
            raise ValueError("Game has already started - cannot join")
        
        if game.status not in [GameStatus.WAITING, GameStatus.COUNTDOWN]:
            raise ValueError("Cannot join game in current state")
        
        # Get permanent cartela from database
        cartela = await self.get_cartela(card_number)
        if not cartela:
            raise ValueError(f"Cartela {card_number} not found. Please initialize cartelas first.")
        
        # Use the permanent card data
        card_data = cartela.card_data
        
        # Validate card follows standard Bingo rules
        if not BingoGameEngine.validate_bingo_card(card_data):
            raise ValueError(f"Cartela {card_number} has invalid card data")
        
        print(f"Using permanent cartela {card_number} for user {user_id}")
        
        # Create player
        player = Player(
            user_id=user_id,
            game_id=game.id,
            card_number=card_number,
            card_data=card_data,
            marked_numbers=[]
        )
        
        self.db.add(player)
        
        # Update game
        game.total_players += 1
        game.prize_pool += game.entry_fee
        
        await self.db.commit()
        await self.db.refresh(player)
        
        # Mark card as taken in Redis
        await redis_client.set_card_status(game_id, card_number, user_id)
        
        # Broadcast game state update to all connected clients
        from .websocket import broadcast_game_state
        await broadcast_game_state(game_id, game.total_players, game.prize_pool)
        
        return player
    
    async def start_countdown(self, game_id: str):
        """Start countdown before game begins"""
        result = await self.db.execute(
            select(Game).where(Game.game_id == game_id)
        )
        game = result.scalar_one_or_none()
        if not game:
            return
        
        game.status = GameStatus.COUNTDOWN
        await self.db.commit()
        
        # Set timer in Redis
        await redis_client.set_timer(game_id, game.countdown_seconds)
    
    async def start_game(self, game_id: str):
        """Start the actual game"""
        result = await self.db.execute(
            select(Game).where(Game.game_id == game_id)
        )
        game = result.scalar_one_or_none()
        if not game:
            return
        
        game.status = GameStatus.ACTIVE
        game.started_at = datetime.utcnow()
        await self.db.commit()
        
        # Update Redis
        await redis_client.set_game_state(game_id, {
            "status": GameStatus.ACTIVE.value,
            "started_at": game.started_at.isoformat()
        })
    
    async def call_number(self, game_id: str) -> Optional[int]:
        """
        Call next number using pop() method (like real Bingo).
        Numbers are popped from pre-shuffled deck in Redis - GUARANTEES no duplicates.
        """
        # Pop next number from shuffled deck in Redis
        number = await redis_client.pop_remaining_number(game_id)
        if number is None:
            return None
        
        # Update Redis
        await redis_client.add_called_number(game_id, number)
        
        print(f"Called number {number}")
        
        return number
    
    async def mark_number_on_all_cards(self, game_id: str, number: int):
        """
        Mark a called number on ALL player cards immediately (like real Bingo).
        This ensures backend state matches frontend display.
        """
        result = await self.db.execute(
            select(Game).where(Game.game_id == game_id)
        )
        game = result.scalar_one_or_none()
        if not game:
            return
        
        # Get all players in this game
        players_result = await self.db.execute(
            select(Player).where(Player.game_id == game.id)
        )
        players = players_result.scalars().all()
        
        # Mark the number on each player's card
        from sqlalchemy.orm.attributes import flag_modified
        
        for player in players:
            # Get current marked numbers
            marked = player.marked_numbers or []
            
            # Mark the number
            marked = BingoGameEngine.mark_number(
                player.card_data,
                marked,
                number
            )
            
            # Reassign to trigger SQLAlchemy change detection
            player.marked_numbers = marked
            
            # Flag as modified for JSON column
            flag_modified(player, "marked_numbers")
        
        # Commit all marks to database
        await self.db.commit()
        print(f"Marked number {number} on {len(players)} player cards")
    
    async def check_winners(self, game_id: str) -> List[Player]:
        """
        Check if any players have won.
        Numbers are already marked by mark_number_on_all_cards(),
        so we just check for winning patterns.
        """
        result = await self.db.execute(
            select(Game).where(Game.game_id == game_id)
        )
        game = result.scalar_one_or_none()
        if not game:
            return []
        
        # Get all players who haven't won yet
        players_result = await self.db.execute(
            select(Player).where(Player.game_id == game.id, Player.has_won.is_(False))
        )
        players = players_result.scalars().all()
        
        winners = []
        for player in players:
            # DEBUG: Print marked numbers
            print(f"Checking player {player.user_id}: {len(player.marked_numbers)} marked")
            print(f"   Marked indices: {player.marked_numbers}")
            
            # Check for win using already-marked numbers
            has_won, pattern = BingoGameEngine.check_win(
                player.card_data,
                player.marked_numbers
            )
            
            if has_won:
                player.has_won = True
                player.winning_pattern = pattern
                winners.append(player)
                print(f"Player {player.user_id} won with pattern: {pattern}")
            else:
                print(f"   No win yet")
        
        if winners:
            await self.db.commit()
        
        return winners
    
    async def finish_game(self, game_id: str, winner_ids: List[int]):
        """Finish the game and distribute prizes (prevents duplicate payouts)"""
        result = await self.db.execute(
            select(Game).where(Game.game_id == game_id)
        )
        game = result.scalar_one_or_none()
        if not game:
            return None
        
        # Prevent duplicate processing
        if game.status == GameStatus.FINISHED:
            print(f"Game {game_id} already finished, skipping payout")
            return None
        
        game.status = GameStatus.FINISHED
        game.finished_at = datetime.utcnow()
        game.winner_ids = winner_ids
        
        if not winner_ids:
            await self.db.commit()
            return 0
        
        # Calculate prize per winner
        commission = game.prize_pool * (settings.COMMISSION_PERCENT / 100)
        total_prize = game.prize_pool - commission
        prize_per_winner = total_prize / len(winner_ids)
        
        print(f"Prize pool: {game.prize_pool} ETB, Commission: {commission} ETB")
        print(f"Prize per winner: {prize_per_winner} ETB ({len(winner_ids)} winner(s))")
        
        # Update winner balances
        for user_id in winner_ids:
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    balance=User.balance + prize_per_winner,
                    wins=User.wins + 1
                )
            )
            print(f"Paid {prize_per_winner} ETB to user {user_id}")
            
            # Update Redis Leaderboard
            await redis_client.increment_leaderboard(user_id)
        
        await self.db.commit()
        
        # Clean up Redis
        await redis_client.remove_active_game(game_id)
        await redis_client.clear_game_cards(game_id)
        await redis_client.clear_called_numbers(game_id)
        
        return prize_per_winner

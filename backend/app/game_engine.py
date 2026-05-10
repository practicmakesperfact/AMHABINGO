import random
import asyncio
from typing import List, Tuple, Optional, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from .models import Game, Player, User, GameStatus
from .redis_client import redis_client
from .config import get_settings

settings = get_settings()

class BingoGameEngine:
    """Core bingo game logic"""
    
    @staticmethod
    def generate_bingo_card() -> List[List[int]]:
        """
        Generate a 5x5 bingo card with numbers 1-75
        B: 1-15, I: 16-30, N: 31-45, G: 46-60, O: 61-75
        Center is FREE (0)
        """
        card = []
        ranges = [
            (1, 15),    # B
            (16, 30),   # I
            (31, 45),   # N
            (46, 60),   # G
            (61, 75)    # O
        ]
        
        for col_idx, (start, end) in enumerate(ranges):
            column = random.sample(range(start, end + 1), 5)
            card.append(column)
        
        # Transpose to get rows
        card = [[card[col][row] for col in range(5)] for row in range(5)]
        
        # Set center as FREE (0)
        card[2][2] = 0
        
        return card
    
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
    def call_next_number(called_numbers: List[int]) -> Optional[int]:
        """Call a random number that hasn't been called yet"""
        available = [n for n in range(1, 76) if n not in called_numbers]
        if not available:
            return None
        return random.choice(available)
    
    @staticmethod
    def mark_number(card: List[List[int]], marked: List[int], number: int) -> List[int]:
        """Mark a number on the card if it exists"""
        for row_idx, row in enumerate(card):
            for col_idx, cell in enumerate(row):
                if cell == number:
                    flat_idx = row_idx * 5 + col_idx
                    if flat_idx not in marked:
                        marked.append(flat_idx)
        return marked
    
    @staticmethod
    def check_win(card: List[List[int]], marked: List[int]) -> Tuple[bool, Optional[str]]:
        """
        Check if the card has a winning pattern
        Returns: (has_won, pattern_type)
        """
        # Convert flat indices to 2D coordinates
        marked_coords = {(idx // 5, idx % 5) for idx in marked}
        
        # Center is always marked (FREE)
        marked_coords.add((2, 2))
        
        # Check rows
        for row in range(5):
            if all((row, col) in marked_coords for col in range(5)):
                return True, f"row_{row}"
        
        # Check columns
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
        """Create a new game"""
        import uuid
        game_id = f"GAME-{uuid.uuid4().hex[:8].upper()}"
        
        game = Game(
            game_id=game_id,
            room=room,
            entry_fee=entry_fee,
            status=GameStatus.WAITING
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
        
        await redis_client.add_active_game(game_id)
        
        return game
    
    async def join_game(self, game_id: str, user_id: int, card_number: int) -> Player:
        """Add player to game"""
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
        
        if game.status != GameStatus.WAITING:
            raise ValueError("Game has already started")
        
        # Generate bingo card
        card_data = BingoGameEngine.generate_bingo_card()
        
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
        """Call next number in the game"""
        result = await self.db.execute(
            select(Game).where(Game.game_id == game_id)
        )
        game = result.scalar_one_or_none()
        if not game or game.status != GameStatus.ACTIVE:
            return None
        
        # Call next number
        number = BingoGameEngine.call_next_number(game.called_numbers)
        if number is None:
            return None
        
        # Update database
        game.called_numbers.append(number)
        game.current_number = number
        await self.db.commit()
        
        # Update Redis
        await redis_client.add_called_number(game_id, number)
        
        return number
    
    async def check_winners(self, game_id: str) -> List[Player]:
        """Check if any players have won"""
        result = await self.db.execute(
            select(Game).where(Game.game_id == game_id)
        )
        game = result.scalar_one_or_none()
        if not game:
            return []
        
        # Get all players
        players_result = await self.db.execute(
            select(Player).where(Player.game_id == game.id, Player.has_won.is_(False))
        )
        players = players_result.scalars().all()
        
        winners = []
        for player in players:
            # Auto-mark the current number
            if game.current_number:
                player.marked_numbers = BingoGameEngine.mark_number(
                    player.card_data,
                    player.marked_numbers,
                    game.current_number
                )
            
            # Check for win
            has_won, pattern = BingoGameEngine.check_win(
                player.card_data,
                player.marked_numbers
            )
            
            if has_won:
                player.has_won = True
                player.winning_pattern = pattern
                winners.append(player)
        
        if winners:
            await self.db.commit()
        
        return winners
    
    async def finish_game(self, game_id: str, winner_ids: List[int]):
        """Finish the game and distribute prizes"""
        result = await self.db.execute(
            select(Game).where(Game.game_id == game_id)
        )
        game = result.scalar_one_or_none()
        if not game:
            return
        
        game.status = GameStatus.FINISHED
        game.finished_at = datetime.utcnow()
        game.winner_ids = winner_ids
        
        # Calculate prize per winner
        commission = game.prize_pool * (settings.COMMISSION_PERCENT / 100)
        prize_per_winner = (game.prize_pool - commission) / len(winner_ids)
        
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
        
        await self.db.commit()
        
        # Clean up Redis
        await redis_client.remove_active_game(game_id)
        await redis_client.clear_game_cards(game_id)
        await redis_client.clear_called_numbers(game_id)
        
        return prize_per_winner

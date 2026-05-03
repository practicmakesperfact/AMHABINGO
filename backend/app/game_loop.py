import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import Game, GameStatus
from .database import AsyncSessionLocal
from .game_engine import GameManager, BingoGameEngine
from .websocket import (
    broadcast_timer_update,
    broadcast_game_started,
    broadcast_number_called,
    broadcast_player_won
)
from .redis_client import redis_client
from .config import get_settings

settings = get_settings()

class GameLoopManager:
    """Manages background game loops"""
    
    def __init__(self):
        self.active_loops = {}
    
    async def start_countdown_loop(self, game_id: str):
        """Start countdown before game begins"""
        if game_id in self.active_loops:
            return
        
        task = asyncio.create_task(self._countdown_loop(game_id))
        self.active_loops[game_id] = task
    
    async def _countdown_loop(self, game_id: str):
        """Countdown loop"""
        async with AsyncSessionLocal() as db:
            game_manager = GameManager(db)
            
            # Get game
            result = await db.execute(
                select(Game).where(Game.game_id == game_id)
            )
            game = result.scalar_one_or_none()
            
            if not game:
                return
            
            # Start countdown
            await game_manager.start_countdown(game_id)
            
            # Countdown timer
            for seconds in range(game.countdown_seconds, 0, -1):
                await broadcast_timer_update(game_id, seconds)
                await asyncio.sleep(1)
            
            # Start game
            await game_manager.start_game(game_id)
            await broadcast_game_started(game_id)
            
            # Start game loop
            await self._game_loop(game_id)
    
    async def _game_loop(self, game_id: str):
        """Main game loop - calls numbers and checks for winners"""
        async with AsyncSessionLocal() as db:
            game_manager = GameManager(db)
            
            while True:
                # Get game
                result = await db.execute(
                    select(Game).where(Game.game_id == game_id)
                )
                game = result.scalar_one_or_none()
                
                if not game or game.status != GameStatus.ACTIVE:
                    break
                
                # Call next number
                number = await game_manager.call_number(game_id)
                
                if number is None:
                    # All numbers called, no winner
                    await game_manager.finish_game(game_id, [])
                    break
                
                # Get category
                category = BingoGameEngine.get_number_category(number)
                
                # Broadcast number
                await broadcast_number_called(game_id, number, category)
                
                # Wait before checking winners
                await asyncio.sleep(1)
                
                # Check for winners
                winners = await game_manager.check_winners(game_id)
                
                if winners:
                    # Finish game
                    winner_ids = [w.user_id for w in winners]
                    prize_per_winner = await game_manager.finish_game(game_id, winner_ids)
                    
                    # Prepare winner data
                    winner_data = []
                    for winner in winners:
                        # Get user info
                        from .models import User
                        user_result = await db.execute(
                            select(User).where(User.id == winner.user_id)
                        )
                        user = user_result.scalar_one_or_none()
                        
                        winner_data.append({
                            "user_id": winner.user_id,
                            "username": user.username if user else None,
                            "card_number": winner.card_number,
                            "winning_pattern": winner.winning_pattern,
                            "prize_amount": prize_per_winner
                        })
                    
                    # Broadcast winners
                    await broadcast_player_won(game_id, winner_data)
                    break
                
                # Wait before calling next number
                await asyncio.sleep(settings.GAME_INTERVAL_SECONDS)
        
        # Clean up
        if game_id in self.active_loops:
            del self.active_loops[game_id]
    
    def stop_game_loop(self, game_id: str):
        """Stop a game loop"""
        if game_id in self.active_loops:
            task = self.active_loops[game_id]
            task.cancel()
            del self.active_loops[game_id]

# Global game loop manager
game_loop_manager = GameLoopManager()

"""Initialize games for all stake levels (10, 20, 50, 100 ETB)"""
import asyncio
from app.database import AsyncSessionLocal
from app.game_engine import GameManager
from app.models import Game, GameStatus
from sqlalchemy import select

STAKE_LEVELS = [10, 20, 50, 100]

async def init_stake_games():
    print("🎮 Initializing games for all stake levels...")
    
    async with AsyncSessionLocal() as db:
        game_manager = GameManager(db)
        
        for stake in STAKE_LEVELS:
            # Check if there's already a waiting/countdown game for this stake
            result = await db.execute(
                select(Game)
                .where(
                    Game.entry_fee == stake,
                    Game.room == "beginner",
                    Game.status.in_([GameStatus.WAITING, GameStatus.COUNTDOWN])
                )
                .order_by(Game.created_at.desc())
                .limit(1)
            )
            existing_game = result.scalar_one_or_none()
            
            if existing_game:
                print(f"✓ Game already exists for {stake} ETB: {existing_game.game_id}")
            else:
                # Create a new game for this stake
                game = await game_manager.create_game("beginner", float(stake))
                print(f"✨ Created game for {stake} ETB: {game.game_id}")
    
    print("✅ All stake levels initialized!")

if __name__ == "__main__":
    asyncio.run(init_stake_games())

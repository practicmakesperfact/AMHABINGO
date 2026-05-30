"""
Cleanup script to finish all active games and reset the database
Run this to stop all the infinite game loops
"""
import asyncio
from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models import Game, GameStatus

async def cleanup():
    async with AsyncSessionLocal() as db:
        # Get all non-finished games
        result = await db.execute(
            select(Game).where(
                Game.status.in_([GameStatus.WAITING, GameStatus.COUNTDOWN, GameStatus.ACTIVE])
            )
        )
        games = result.scalars().all()
        
        print(f"Found {len(games)} active games")
        
        # Mark all as finished
        for game in games:
            game.status = GameStatus.FINISHED
            print(f"Finishing game: {game.game_id}")
        
        await db.commit()
        print("✅ All games finished")

if __name__ == "__main__":
    asyncio.run(cleanup())

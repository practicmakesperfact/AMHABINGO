"""
Migration: Add remaining_numbers field to games table.
This enables the pop() method for calling numbers (like real Bingo).

SIMPLE APPROACH:
1. Just restart the backend - SQLAlchemy will add the column automatically
2. This script populates existing games with shuffled decks
"""
import asyncio
import sys
import os
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal, init_db
from app.models import Game, GameStatus
from sqlalchemy import select, text


async def migrate():
    """Populate remaining_numbers for existing games"""
    print("🔄 Starting migration: Populate remaining_numbers field")
    
    # Initialize database (this will create the column if it doesn't exist)
    await init_db()
    
    print("✅ Database initialized (column created if needed)")
    
    async with AsyncSessionLocal() as db:
        # Get all games
        result = await db.execute(select(Game))
        all_games = result.scalars().all()
        
        if not all_games:
            print("✅ No games to migrate")
            return
        
        print(f"📊 Found {len(all_games)} game(s) to check")
        
        updated = 0
        for game in all_games:
            # Check if remaining_numbers is empty or None
            if not game.remaining_numbers:
                # Create shuffled deck excluding already called numbers
                called = game.called_numbers or []
                remaining = [n for n in range(1, 76) if n not in called]
                random.shuffle(remaining)
                
                game.remaining_numbers = remaining
                updated += 1
                
                print(f"  ✅ Game {game.game_id}: {len(called)} called, {len(remaining)} remaining")
            else:
                print(f"  ⏭️  Game {game.game_id}: Already has remaining_numbers")
        
        if updated > 0:
            await db.commit()
            print(f"\n✅ Migration complete! Updated {updated} game(s)")
        else:
            print(f"\n✅ No games needed updating")


async def verify():
    """Verify migration was successful"""
    print("\n🔍 Verifying migration...")
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Game).limit(5))
        games = result.scalars().all()
        
        for game in games:
            remaining = game.remaining_numbers or []
            called = game.called_numbers or []
            
            print(f"\nGame {game.game_id}:")
            print(f"  Status: {game.status}")
            print(f"  Called: {len(called)} numbers")
            print(f"  Remaining: {len(remaining)} numbers")
            
            if game.status == GameStatus.ACTIVE:
                # Check for duplicates
                all_nums = set(called + remaining)
                if len(all_nums) != len(called) + len(remaining):
                    print(f"  ⚠️  WARNING: Duplicate numbers detected!")
                else:
                    print(f"  ✅ No duplicates")


if __name__ == "__main__":
    print("="*60)
    print("MIGRATION: Add remaining_numbers field")
    print("="*60)
    
    asyncio.run(migrate())
    asyncio.run(verify())
    
    print("\n" + "="*60)
    print("✅ MIGRATION COMPLETE")
    print("="*60)
    print("\n📝 Next steps:")
    print("1. Restart backend: python -m uvicorn app.main:app --reload")
    print("2. Test game: Numbers should be called without duplicates")
    print("3. Check logs: Should see 'Remaining: X/75' after each call")

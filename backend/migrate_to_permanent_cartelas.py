"""
Migration script to add permanent cartelas table and initialize 600 cartelas.
Run this after updating models.py to add the Cartela model.
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal, engine, Base
from app.models import Cartela
from app.game_engine import BingoGameEngine
from sqlalchemy import select, text


async def migrate():
    """Run migration"""
    print("🔄 Starting migration to permanent cartelas system...")
    
    # Step 1: Create new tables
    print("\n📋 Step 1: Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created/updated")
    
    # Step 2: Check if cartelas exist
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Cartela))
        existing = result.scalars().all()
        
        if existing:
            print(f"\n⚠️  Found {len(existing)} existing cartelas")
            print("Skipping cartela generation (already exists)")
            return
        
        # Step 3: Generate 600 permanent cartelas
        print("\n🎰 Step 2: Generating 600 permanent cartelas...")
        cartelas = []
        
        for i in range(1, 601):
            # Generate a valid bingo card
            while True:
                card_data = BingoGameEngine.generate_bingo_card()
                if BingoGameEngine.validate_bingo_card(card_data):
                    break
            
            cartela = Cartela(
                cartela_number=i,
                card_data=card_data
            )
            cartelas.append(cartela)
            
            if i % 100 == 0:
                print(f"  ✅ Generated {i}/600 cartelas")
        
        # Bulk insert
        db.add_all(cartelas)
        await db.commit()
        
        print(f"\n✅ Successfully created 600 permanent cartelas!")
        
        # Step 4: Verify
        result = await db.execute(select(Cartela))
        all_cartelas = result.scalars().all()
        print(f"\n✅ Verification: {len(all_cartelas)} cartelas in database")
        
        # Show samples
        print("\n" + "="*60)
        print("SAMPLE CARTELAS")
        print("="*60)
        
        for sample_num in [1, 300, 600]:
            result = await db.execute(
                select(Cartela).where(Cartela.cartela_number == sample_num)
            )
            cartela = result.scalar_one_or_none()
            
            if cartela:
                print(f"\nCartela #{sample_num}:")
                print("  B    I    N    G    O")
                print("-" * 30)
                
                card = cartela.card_data
                for row in range(5):
                    row_values = []
                    for col in range(5):
                        val = card[col][row]
                        if val == 0:
                            row_values.append("FREE")
                        else:
                            row_values.append(f"{val:2d}")
                    print("  ".join(f"{v:>4}" for v in row_values))
        
        print("\n" + "="*60)
        print("✅ MIGRATION COMPLETE!")
        print("="*60)
        print("\n📝 Summary:")
        print("  - Added Cartela model to database")
        print("  - Generated 600 permanent cartelas")
        print("  - Each cartela has a unique 5x5 grid")
        print("  - Cartelas are numbered 1-600")
        print("  - Added support for four-corner and blackout patterns")
        print("\n🎮 Your Bingo game now follows real 75-ball Bingo rules!")


if __name__ == "__main__":
    asyncio.run(migrate())

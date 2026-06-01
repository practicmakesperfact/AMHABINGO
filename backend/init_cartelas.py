"""
Initialize 600 permanent cartelas in the database.
Each cartela has a unique, permanently stored 5x5 bingo card.
Run this once after database setup.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal, init_db
from app.models import Cartela
from app.game_engine import BingoGameEngine
from sqlalchemy import select


async def init_cartelas():
    """Generate and store 600 permanent cartelas"""
    print("🎲 Initializing 600 permanent cartelas...")
    
    # Ensure database tables exist
    await init_db()
    
    async with AsyncSessionLocal() as db:
        # Check if cartelas already exist
        result = await db.execute(select(Cartela))
        existing = result.scalars().all()
        
        if existing:
            print(f"⚠️  Found {len(existing)} existing cartelas")
            response = input("Do you want to regenerate all cartelas? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Aborted")
                return
            
            # Delete existing cartelas
            for cartela in existing:
                await db.delete(cartela)
            await db.commit()
            print("🗑️  Deleted existing cartelas")
        
        # Generate 600 unique cartelas
        print("🎰 Generating 600 unique bingo cards...")
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
        print(f"📊 Each cartela has a unique 5x5 grid stored in the database")
        print(f"🎯 Cartelas are numbered 1-600")
        
        # Show sample cartelas
        print("\n" + "="*60)
        print("SAMPLE CARTELAS")
        print("="*60)
        
        for sample_num in [1, 100, 300, 600]:
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


if __name__ == "__main__":
    asyncio.run(init_cartelas())

import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    print("Starting migration...")
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN phone_number VARCHAR;"))
            print("Added phone_number")
        except Exception as e:
            print(f"Error adding phone_number: {e}")
            
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN play_balance FLOAT DEFAULT 0.0;"))
            print("Added play_balance")
        except Exception as e:
            print(f"Error adding play_balance: {e}")
            
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0;"))
            print("Added coins")
        except Exception as e:
            print(f"Error adding coins: {e}")

    print("Migration complete!")

if __name__ == "__main__":
    asyncio.run(migrate())

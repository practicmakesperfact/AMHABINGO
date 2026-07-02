import asyncio
import os
import sys

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal, engine
from app.models import User
from sqlalchemy import select

async def main():
    print("Connecting to database...")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"Found {len(users)} users in database.")
        for user in users:
            old_balance = user.balance
            user.balance += 1000.0
            print(f"User: {user.username or user.first_name} (ID: {user.id}, Telegram ID: {user.telegram_id}) - Balance updated from {old_balance} to {user.balance}")
        await session.commit()
        print("Balances successfully updated!")

if __name__ == "__main__":
    asyncio.run(main())

"""Initialize PostgreSQL database tables"""
import asyncio
from app.database import init_db

async def main():
    print("🔧 Initializing database...")
    await init_db()
    print("✅ Done! Database is ready.")

if __name__ == "__main__":
    asyncio.run(main())

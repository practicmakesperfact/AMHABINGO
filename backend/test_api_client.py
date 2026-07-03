"""
Test script to verify BotAPIClient works correctly.
Run this to ensure the architecture fix is working.

Usage:
    python test_api_client.py
"""

import asyncio
from bot_api_client import BotAPIClient
from app.config import get_settings

settings = get_settings()


async def test_api_client():
    """Test all BotAPIClient methods."""
    
    print("🧪 Testing BotAPIClient...")
    print(f"📍 Backend URL: {settings.BACKEND_URL}\n")
    
    api_client = BotAPIClient(settings.BACKEND_URL)
    
    try:
        # Test 1: Register User
        print("1️⃣ Testing user registration...")
        try:
            user = await api_client.register_user(
                telegram_id=999888777,
                phone_number="+251911223344",
                username="test_user",
                first_name="Test",
                last_name="User"
            )
            print(f"   ✅ User registered: {user.get('first_name')} (ID: {user.get('id')})")
            print(f"   💰 Balance: {user.get('balance')} ETB")
            print(f"   🎮 Play Balance: {user.get('play_balance')} ETB\n")
        except Exception as e:
            print(f"   ❌ Registration failed: {e}\n")
        
        # Test 2: Get User by Telegram ID
        print("2️⃣ Testing get user by telegram_id...")
        try:
            user = await api_client.get_user_by_telegram_id(999888777)
            if user:
                print(f"   ✅ User found: {user.get('username')}")
                print(f"   📱 Phone: {user.get('phone_number')}\n")
            else:
                print(f"   ℹ️  User not found\n")
        except Exception as e:
            print(f"   ❌ Get user failed: {e}\n")
        
        # Test 3: Get Balance
        print("3️⃣ Testing get balance...")
        try:
            balance = await api_client.get_user_balance(999888777)
            print(f"   ✅ Balance retrieved:")
            print(f"   💰 Main: {balance.get('balance')} ETB")
            print(f"   🎮 Play: {balance.get('play_balance')} ETB")
            print(f"   🪙 Coins: {balance.get('coins')}")
            print(f"   💵 Total: {balance.get('total')} ETB\n")
        except Exception as e:
            print(f"   ❌ Get balance failed: {e}\n")
        
        # Test 4: Get Transactions
        print("4️⃣ Testing get transactions...")
        try:
            transactions = await api_client.get_transactions(999888777, limit=10)
            print(f"   ✅ Transactions retrieved: {len(transactions)} found\n")
        except Exception as e:
            print(f"   ❌ Get transactions failed: {e}\n")
        
        # Test 5: Health Check (bonus test)
        print("5️⃣ Testing backend health...")
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{settings.BACKEND_URL}/health")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Backend is healthy")
                    print(f"   📊 Status: {data.get('status')}")
                    print(f"   🔴 Redis: {data.get('redis')}")
                    print(f"   🗄️  Database: {data.get('database')}")
                    print(f"   ⏱️  Uptime: {data.get('uptime_seconds')}s\n")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}\n")
        
        print("=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        print("\n💡 Next steps:")
        print("   1. Start FastAPI: uvicorn app.main:app --reload")
        print("   2. Start Bot: python bot.py")
        print("   3. Test in Telegram: Click 'Register 📋'\n")
        
    finally:
        await api_client.close()
        print("🔌 API client closed")


if __name__ == "__main__":
    asyncio.run(test_api_client())


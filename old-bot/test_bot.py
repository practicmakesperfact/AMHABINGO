import os
from dotenv import load_dotenv
import httpx

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

def test_bot():
    """Test if bot token is valid and bot is accessible"""
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    try:
        # Get bot info
        response = httpx.get(f"{base_url}/getMe", timeout=10)
        result = response.json()
        
        if result.get('ok'):
            bot_info = result['result']
            print("✅ Bot is valid and accessible!")
            print(f"   Bot Name: {bot_info['first_name']}")
            print(f"   Username: @{bot_info['username']}")
            print(f"   Bot ID: {bot_info['id']}")
            print(f"\n🔗 Start chatting: https://t.me/{bot_info['username']}")
        else:
            print("❌ Bot token is invalid!")
            print(f"   Error: {result}")
    except Exception as e:
        print(f"❌ Error connecting to bot: {e}")

if __name__ == "__main__":
    test_bot()

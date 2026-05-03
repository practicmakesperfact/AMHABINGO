import os
from dotenv import load_dotenv
import httpx

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

def clear_webhook():
    """Clear webhook and drop pending updates"""
    base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
    
    # Delete webhook
    response = httpx.get(f"{base_url}/deleteWebhook?drop_pending_updates=true")
    print(f"Delete webhook: {response.json()}")
    
    # Get updates with offset=-1 to clear queue
    response = httpx.get(f"{base_url}/getUpdates?offset=-1")
    print(f"Clear updates: {response.json()}")

if __name__ == "__main__":
    clear_webhook()
    print("\n✅ Webhook cleared! Now you can run: python bot.py")

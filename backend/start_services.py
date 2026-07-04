#!/usr/bin/env python3
"""
Start both bot and backend services together.
This ensures both run properly on Render free tier.
"""

import subprocess
import sys
import time
import os

def start_bot():
    """Start the Telegram bot in background."""
    print("🤖 Starting Telegram Bot...")
    try:
        # Start bot as subprocess
        bot_process = subprocess.Popen(
            [sys.executable, "bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        print(f"✅ Bot started with PID: {bot_process.pid}")
        return bot_process
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        return None

def start_backend():
    """Start the FastAPI backend."""
    print("🌐 Starting FastAPI Backend...")
    port = os.getenv("PORT", "10000")
    
    # Start uvicorn (this blocks)
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", port
    ])

if __name__ == "__main__":
    print("🚀 Starting AMHABINGO services...")
    
    # Start bot in background
    bot_process = start_bot()
    
    # Give bot a moment to initialize
    time.sleep(2)
    
    # Start backend (this will block)
    try:
        start_backend()
    finally:
        # If backend stops, stop bot too
        if bot_process:
            print("🛑 Stopping bot...")
            bot_process.terminate()
            bot_process.wait()

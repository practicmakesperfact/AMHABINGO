#!/bin/bash

echo "🚀 Starting AMHABINGO services..."

# Start bot in background
echo "🤖 Starting Telegram Bot..."
python bot.py &
BOT_PID=$!
echo "✅ Bot started with PID: $BOT_PID"

# Start FastAPI server
echo "🌐 Starting FastAPI Backend..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT

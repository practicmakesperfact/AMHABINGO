#!/bin/bash

echo "🚀 Starting AMHABINGO Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your credentials before running again!"
    exit 1
fi

# Start the server
echo "✅ Starting FastAPI server..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

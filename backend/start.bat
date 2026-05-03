@echo off
echo 🚀 Starting AMHABINGO Backend...

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found!
    echo 📝 Creating .env from .env.example...
    copy .env.example .env
    echo ⚠️  Please edit .env with your credentials before running again!
    pause
    exit /b 1
)

REM Start the server
echo ✅ Starting FastAPI server...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

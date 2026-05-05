@echo off
echo ========================================
echo   AMHABINGO Backend - Simple Start
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo Creating .env file from example...
    copy .env.example .env
    echo.
    echo Please edit .env file with your settings
    echo Press any key to continue after editing...
    pause
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
pip install aiosqlite
echo.

REM Start server
echo Starting backend server...
echo Backend will be available at: http://localhost:8000
echo API docs at: http://localhost:8000/docs
echo.
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause

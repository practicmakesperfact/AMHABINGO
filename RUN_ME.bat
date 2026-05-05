@echo off
echo ========================================
echo   AMHABINGO - Quick Start
echo ========================================
echo.
echo This will start the backend server.
echo After backend starts, open a NEW terminal and run frontend.
echo.
pause

cd backend

REM Create .env if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy /Y .env.example .env
)

echo.
echo Starting backend server...
echo Backend will be at: http://localhost:8000
echo API docs at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause

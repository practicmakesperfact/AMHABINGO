@echo off
echo ========================================
echo   AMHABINGO - Frontend
echo ========================================
echo.
echo Starting frontend...
echo.

cd frontend

REM Create .env.local if it doesn't exist
if not exist .env.local (
    echo Creating .env.local file...
    copy /Y .env.local.example .env.local
)

echo.
echo Frontend will be at: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo.

npm run dev

pause

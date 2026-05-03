@echo off
echo 🎨 Setting up AMHABINGO Frontend...

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js is not installed. Please install Node.js 18+ first.
    pause
    exit /b 1
)

echo ✅ Node.js installed
node --version

REM Install dependencies
echo 📦 Installing dependencies...
call npm install

REM Create .env.local if it doesn't exist
if not exist ".env.local" (
    echo 📝 Creating .env.local...
    copy .env.local.example .env.local
    echo ⚠️  Please edit .env.local with your backend URL!
)

echo.
echo ✅ Setup complete!
echo.
echo 🚀 To start the development server:
echo    npm run dev
echo.
echo 📱 Frontend will be available at: http://localhost:3000
echo.
pause

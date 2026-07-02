# 🚀 Setup Without Docker (Windows)

## Quick Start (SQLite + In-Memory Redis)

This is the easiest way to run the backend without installing PostgreSQL or Redis.

### Step 1: Create .env file

```bash
cd backend
copy .env.example .env
```

Edit `.env` with these values:

```env
# Database (SQLite - no installation needed)
DATABASE_URL=sqlite+aiosqlite:///./bingo.db

# Redis (will use in-memory fallback)
REDIS_URL=redis://localhost:6379

# Telegram (use test values for now)
BOT_TOKEN=test_bot_token
TELEGRAM_BOT_SECRET=test_secret


# App Settings
SECRET_KEY=your-super-secret-key-change-this
COMMISSION_PERCENT=10
GAME_INTERVAL_SECONDS=4

# CORS
FRONTEND_URL=http://localhost:3000
```

### Step 2: Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Install additional package for SQLite

```bash
pip install aiosqlite
```

### Step 4: Run the backend

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run at: http://localhost:8000

---

## Option 2: Install PostgreSQL & Redis Locally

If you want the full production setup:

### Install PostgreSQL

1. Download from: https://www.postgresql.org/download/windows/
2. Run installer (choose default port 5432)
3. Set password (remember it!)
4. Create database:
   ```bash
   # Open SQL Shell (psql)
   CREATE DATABASE bingo;
   CREATE USER bingo WITH PASSWORD 'bingo123';
   GRANT ALL PRIVILEGES ON DATABASE bingo TO bingo;
   ```

5. Update .env:
   ```env
   DATABASE_URL=postgresql+asyncpg://bingo:bingo123@localhost:5432/bingo
   ```

### Install Redis

**Option A: Redis for Windows (Unofficial)**
1. Download from: https://github.com/microsoftarchive/redis/releases
2. Extract and run `redis-server.exe`

**Option B: Use Memurai (Redis alternative for Windows)**
1. Download from: https://www.memurai.com/
2. Install and start service

**Option C: Skip Redis (Use in-memory fallback)**
- The app will work without Redis, but real-time features will be limited

---

## Troubleshooting

### SQLite Issues

If you get errors with SQLite, make sure:
```bash
pip install aiosqlite
```

### Redis Connection Errors

If Redis is not available, the app will still run but WebSocket features may be limited. To fix:
1. Install Redis (see above)
2. Or modify code to use in-memory storage

### Database Migration

First time running, create tables:
```bash
# The app will auto-create tables on first run
# Or manually:
python -c "from app.database import engine, Base; from app.models import *; Base.metadata.create_all(bind=engine)"
```

---

## Testing Without Docker

```bash
# 1. Start backend
cd backend
python -m uvicorn app.main:app --reload

# 2. In another terminal, start frontend
cd frontend
npm run dev

# 3. Open browser
http://localhost:3000
```

---

## What Works Without Docker

✅ **Works:**
- API endpoints
- Database operations (SQLite)
- User authentication
- Game logic
- Frontend connection

⚠️ **Limited:**
- Real-time WebSocket (needs Redis for multi-instance)
- Background tasks (works but not distributed)

🚀 **For Production:**
- Use Docker or cloud services (Supabase, Upstash)
- See DEPLOYMENT_GUIDE.md

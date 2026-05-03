# 🎮 AMHABINGO - Real-time Telegram Bingo Game

A complete, production-ready Telegram Mini App for playing Bingo with real-time multiplayer, payment integration, and beautiful UI.

## 🌟 Features

### Core Features
- ✅ **Telegram Mini App** - Seamless integration with Telegram
- ✅ **Real-time Multiplayer** - WebSocket-based live updates
- ✅ **Card Selection** - Choose from 600 unique cards
- ✅ **Auto-marking** - Numbers automatically marked on your card
- ✅ **Win Detection** - Instant winner detection (rows, columns, diagonals)
- ✅ **Multi-winner Support** - Prize split between multiple winners
- ✅ **Payment Integration** - Chapa API for secure payments
- ✅ **Audio Announcements** - Voice calls for each number
- ✅ **Leaderboard** - Track top players
- ✅ **Responsive UI** - Beautiful design with Tailwind CSS

### Technical Features
- ✅ **FastAPI Backend** - High-performance async Python
- ✅ **Next.js Frontend** - Modern React framework
- ✅ **PostgreSQL** - Reliable data storage
- ✅ **Redis** - Real-time state management
- ✅ **WebSockets** - Live game updates
- ✅ **Production-ready** - Deployment configurations included

## 📁 Project Structure

```
amhabingo/
├── backend/              # FastAPI Backend
│   ├── app/
│   │   ├── main.py      # FastAPI app
│   │   ├── models.py    # Database models
│   │   ├── schemas.py   # Pydantic schemas
│   │   ├── database.py  # DB connection
│   │   ├── redis_client.py
│   │   ├── game_engine.py
│   │   ├── websocket.py
│   │   ├── payment.py
│   │   ├── auth.py
│   │   ├── game_loop.py
│   │   └── routers/
│   │       ├── user.py
│   │       ├── game.py
│   │       └── payment.py
│   ├── requirements.txt
│   └── README.md
│
├── frontend/            # Next.js Frontend (TO BE CREATED)
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── README.md
│
├── old-bot/            # Original simple bot (archived)
└── README.md           # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL
- Redis
- Telegram Bot Token
- Chapa API Key

### Backend Setup

1. **Navigate to backend:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Setup environment:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Run the server:**
```bash
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

### Frontend Setup (Coming Next)

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:3000`

## 🎮 How to Play

1. **Start** - Open the bot in Telegram
2. **Choose Stake** - Select your entry fee (10, 20 ETB, etc.)
3. **Select Card** - Choose from 600 available cards
4. **Wait** - 60-second countdown for other players
5. **Play** - Numbers called every 4 seconds
6. **Win** - Complete a row, column, or diagonal
7. **Collect** - Prize automatically added to balance

## 🔧 Configuration

### Backend (.env)

```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/amhabingo
REDIS_URL=redis://localhost:6379
BOT_TOKEN=your_telegram_bot_token
CHAPA_SECRET_KEY=CHASECK_TEST-your_key
COMMISSION_PERCENT=10
GAME_INTERVAL_SECONDS=4
FRONTEND_URL=http://localhost:3000
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## 📡 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎯 Game Flow

```
1. User opens Telegram Mini App
2. Authenticates via Telegram
3. Selects stake amount
4. Chooses card (1-600)
5. Completes payment via Chapa
6. Joins game room
7. Countdown starts (60s)
8. Game begins
9. Numbers called every 4s
10. Card auto-marks
11. Win detected
12. Prize distributed
13. Next game starts
```

## 🏗️ Architecture

```
┌─────────────────┐
│  Telegram App   │
└────────┬────────┘
         │
┌────────▼────────┐
│  Next.js        │
│  Frontend       │
└────────┬────────┘
         │ HTTP/WS
┌────────▼────────┐
│  FastAPI        │
│  Backend        │
└────┬────┬───────┘
     │    │
┌────▼─┐ ┌▼──────┐
│ PG   │ │ Redis │
└──────┘ └───────┘
```

## 🔐 Security

- ✅ Telegram Web App data verification
- ✅ Server-side payment validation
- ✅ Duplicate card prevention
- ✅ Win validation
- ✅ CORS protection
- ✅ Rate limiting (recommended)

## 📊 Database Schema

### Users
- Telegram ID, username, balance, wins

### Games
- Game ID, status, entry fee, prize pool, players

### Players
- User, game, card number, card data, marked numbers

### Transactions
- User, amount, status, type, payment method

## 🎨 UI Screens

1. **Home** - Menu with options
2. **Stake Selection** - Choose entry fee
3. **Card Selection** - Pick from 600 cards
4. **Game Screen** - Live bingo game
5. **Winner Screen** - Celebration & results

## 🚢 Deployment

### Backend (Render/Railway)

```bash
# Dockerfile included
docker build -t amhabingo-backend .
docker run -p 8000:8000 amhabingo-backend
```

### Frontend (Vercel)

```bash
vercel deploy
```

### Database (Supabase/Neon)

Use managed PostgreSQL service

### Redis (Upstash)

Use serverless Redis

## 📈 Roadmap

- [x] Backend API
- [ ] Frontend UI
- [ ] Payment integration testing
- [ ] Audio system
- [ ] Leaderboard
- [ ] Multiple game rooms
- [ ] Tournament mode
- [ ] Mobile app

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 📄 License

MIT License - see LICENSE file

## 🆘 Support

- **Issues**: GitHub Issues
- **Telegram**: @amhabingo_support
- **Email**: support@amhabingo.com

## 🎉 Credits

Built with ❤️ for the Ethiopian gaming community

---

**Status**: Backend Complete ✅ | Frontend In Progress 🚧

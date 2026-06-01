# 🎮 AMHABINGO - Real-time Telegram Bingo Game

A complete, production-ready Telegram Mini App for playing Bingo with real-time multiplayer, payment integration, and beautiful UI.

## 🌟 Features

### Core Features
- ✅ **Telegram Mini App** - Seamless integration with Telegram
- ✅ **Real-time Multiplayer** - WebSocket-based live updates
- ✅ **600 Permanent Cartelas** - Each with unique 5×5 bingo card (24 numbers + FREE space)
- ✅ **Standard 75-Ball Bingo** - Numbers 1-75, called randomly without repetition
- ✅ **Auto-marking** - Numbers automatically marked on your card
- ✅ **Multiple Win Patterns** - Rows, columns, diagonals, four-corner, blackout
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
├── backend/              # FastAPI Backend ✅
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
├── frontend/            # Next.js Frontend ✅
│   ├── app/            # Pages (App Router)
│   │   ├── page.tsx    # Home
│   │   ├── stake/      # Stake selection
│   │   ├── cards/      # Card selection (1-600)
│   │   ├── game/       # Active game screen
│   │   └── winner/     # Winner page
│   ├── components/     # React components
│   │   ├── BingoCard.tsx
│   │   ├── CalledNumbers.tsx
│   │   ├── Timer.tsx
│   │   ├── WinnerModal.tsx
│   │   └── Loading.tsx
│   ├── lib/           # Core libraries
│   │   ├── api.ts     # API client
│   │   ├── websocket.ts
│   │   ├── telegram.ts
│   │   └── audio.ts   # Web Speech API
│   ├── store/         # Zustand state
│   │   └── gameStore.ts
│   ├── hooks/         # Custom hooks
│   │   ├── useWebSocket.ts
│   │   └── useTelegram.ts
│   └── FRONTEND_STATUS.md
│
├── DEPLOYMENT_GUIDE.md # Production deployment
├── prompt2.md          # Original project spec
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

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows | source venv/bin/activate (Linux/Mac)
pip install -r requirements.txt
cp .env.example .env  # Edit with your credentials
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend: `http://localhost:8000` | API Docs: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local  # Edit with backend URLs
npm run dev
```

Frontend: `http://localhost:3000`

### Testing

1. Start backend (port 8000)
2. Start frontend (port 3000)
3. Open browser: `http://localhost:3000`
4. Test game flow: Home → Stake → Cards → Game → Winner

## 🎮 How to Play

1. **Start** - Open the bot in Telegram
2. **Choose Stake** - Select your entry fee (10, 20 ETB, etc.)
3. **Select Cartela** - Choose from 600 permanent cartelas (each has a unique 5×5 grid with 24 numbers + FREE center space)
4. **Wait** - 60-second countdown for other players
5. **Play** - Numbers 1-75 called randomly every 4 seconds (no repeats)
6. **Win** - Complete a pattern: row, column, diagonal, four-corner, or blackout
7. **Collect** - Prize automatically added to balance

### Bingo Card Structure
Each cartela has a standard 5×5 grid:
- **B column** (1-15): 5 numbers
- **I column** (16-30): 5 numbers  
- **N column** (31-45): 4 numbers + FREE center space
- **G column** (46-60): 5 numbers
- **O column** (61-75): 5 numbers

**Total:** 24 unique numbers + 1 FREE space = 25 cells

### Winning Patterns
- **Horizontal:** Any complete row (5 cells)
- **Vertical:** Any complete column (5 cells)
- **Diagonal:** Corner to corner (5 cells)
- **Four Corner:** All 4 corner cells
- **Blackout:** All 25 cells marked

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

1. **Home** - Menu with play button, balance, leaderboard
2. **Stake Selection** - Choose entry fee (Beginner/Pro/VIP)
3. **Card Selection** - Pick from 600 cards with real-time availability
4. **Game Screen** - Live bingo game with:
   - 5x5 Bingo card with auto-marking
   - Called numbers by category (B-I-N-G-O)
   - Current number highlighted
   - Timer countdown
   - Audio announcements
   - Claim win button
5. **Winner Screen** - Celebration & prize display

## 🔊 Audio System

- **Web Speech API** - Text-to-speech announcements
- **Announcements**:
  - "Game starting! Good luck!"
  - "B 5", "I 22", "N 37", etc.
  - "Bingo! We have a winner!"
- **Toggle** - Enable/disable anytime during game

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
- [x] Frontend UI
- [x] Real-time WebSocket
- [x] Card selection (1-600)
- [x] Auto-marking system
- [x] Audio announcements
- [x] Winner detection
- [ ] Payment integration testing
- [ ] Balance management page
- [ ] Leaderboard page
- [ ] Game history
- [ ] Multiple game rooms
- [ ] Tournament mode
- [ ] Push notifications
- [ ] Mobile app (React Native)

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

**Status**: Backend Complete ✅ | Frontend Complete ✅ | Ready for Testing 🧪

**See Also**:
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment guide
- [frontend/FRONTEND_STATUS.md](frontend/FRONTEND_STATUS.md) - Frontend implementation details
- [prompt2.md](prompt2.md) - Original project specification

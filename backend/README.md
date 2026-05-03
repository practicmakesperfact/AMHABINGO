# AMHABINGO Backend

FastAPI backend for AMHABINGO - Real-time Telegram Bingo Game

## Features

- ✅ FastAPI async framework
- ✅ PostgreSQL database with SQLAlchemy
- ✅ Redis for real-time state management
- ✅ WebSocket support for live updates
- ✅ Chapa payment integration
- ✅ Telegram Web App authentication
- ✅ Game engine with win detection
- ✅ Multi-winner support

## Prerequisites

- Python 3.10+
- PostgreSQL
- Redis

## Installation

1. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Setup environment variables:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Setup database:**

Create PostgreSQL database:
```sql
CREATE DATABASE amhabingo;
```

The tables will be created automatically on first run.

## Configuration

Edit `.env` file:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/amhabingo

# Redis
REDIS_URL=redis://localhost:6379

# Telegram
BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_SECRET=your_bot_secret

# Chapa
CHAPA_SECRET_KEY=CHASECK_TEST-your_key
CHAPA_WEBHOOK_SECRET=your_webhook_secret

# App
SECRET_KEY=your-secret-key-change-in-production
COMMISSION_PERCENT=10
GAME_INTERVAL_SECONDS=4

# CORS
FRONTEND_URL=http://localhost:3000
```

## Running the Server

**Development mode:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Production mode:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Endpoints

### Health Check
- `GET /` - Basic health check
- `GET /health` - Detailed health check

### Users
- `POST /api/users/auth` - Authenticate via Telegram
- `GET /api/users/me` - Get current user
- `GET /api/users/{user_id}` - Get user by ID

### Games
- `POST /api/games/` - Create new game
- `GET /api/games/` - List games
- `GET /api/games/{game_id}` - Get game details
- `GET /api/games/{game_id}/players` - Get game players
- `GET /api/games/{game_id}/available-cards` - Get available cards
- `POST /api/games/{game_id}/join` - Join game
- `WS /api/games/ws/{game_id}` - WebSocket connection

### Payments
- `POST /api/payments/initialize` - Initialize payment
- `POST /api/payments/verify` - Verify payment
- `GET /api/payments/transactions` - Get transaction history

## WebSocket Events

### Client → Server
```json
{
  "type": "select_card",
  "data": {"card_number": 42}
}
```

### Server → Client
```json
{
  "type": "card_selected",
  "data": {"card_number": 42, "user_id": 123}
}

{
  "type": "timer_update",
  "data": {"seconds": 30}
}

{
  "type": "number_called",
  "data": {"number": 15, "category": "B"}
}

{
  "type": "player_won",
  "data": {
    "winners": [
      {
        "user_id": 123,
        "username": "player1",
        "card_number": 42,
        "winning_pattern": "row_2",
        "prize_amount": 450.0
      }
    ]
  }
}
```

## Database Schema

### Users
- id, telegram_id, username, first_name, last_name
- balance, wins, games_played
- created_at, updated_at

### Games
- id, game_id, status, room, entry_fee
- prize_pool, total_players, max_players
- called_numbers, current_number, winner_ids
- countdown_seconds, created_at, started_at, finished_at

### Players
- id, user_id, game_id, card_number
- card_data (JSON), marked_numbers (JSON)
- has_won, winning_pattern, joined_at

### Transactions
- id, user_id, game_id, amount, tx_ref
- status, type, payment_method, metadata
- created_at, updated_at

## Redis Keys

- `game:{game_id}` - Game state
- `game:{game_id}:cards` - Card availability (hash)
- `game:{game_id}:timer` - Countdown timer
- `game:{game_id}:called` - Called numbers (list)
- `active_games` - Set of active game IDs
- `session:{user_id}` - User session data

## Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using Render/Railway

1. Connect your GitHub repo
2. Set environment variables
3. Deploy!

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## License

MIT

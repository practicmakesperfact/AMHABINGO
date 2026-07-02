You are a senior full-stack engineer. Build a complete real-time Bingo Telegram Mini App called "AMHABINGO" similar to Beteseb Bingo.

TECH STACK:
- Frontend: Next.js (App Router,Tailwind CSS)
- Backend: FastAPI (async)
- Database: PostgreSQL
- Real-time: Redis + WebSockets
- Deployment-ready structure

---

CORE FEATURES:

1. TELEGRAM MINI APP INTEGRATION
- Use Telegram Web App SDK
- Get user info from Telegram (initDataUnsafe)
- Full-screen responsive UI
- Secure user authentication via Telegram

---

2. GAME SYSTEM

Game lifecycle:
- waiting → countdown → active → finished

Each game includes:
- game_id
- room (beginner, pro, vip)
- entry_fee
- players
- prize_pool
- called_numbers
- current_number
- timer

---

3. CARD SELECTION SYSTEM (1–600)

- Display 600 selectable cards
- Card states:
  - available (purple)
  - selected by user (green)
  - taken by others (red)
- Real-time updates using WebSocket
- 60-second countdown before locking cards

---

4. REAL-TIME SYSTEM (WebSocket)

Implement WebSocket events:

Server → Client:
- card_selected
- timer_update
- game_started
- number_called
- player_won

Client → Server:
- select_card
- join_game
- claim_win

---

5. BINGO GAME ENGINE

- Generate numbers (1–75, no repeat)
- Call number every 3–5 seconds
- Auto-mark numbers on player cards
- Detect win:
  - row
  - column
  - diagonal

- Stop game when winner found

---

6. AUDIO SYSTEM

- Announce numbers using:
  - browser speech synthesis OR
  - pre-recorded audio files

---

7. DATABASE DESIGN (PostgreSQL)

Users:
- id
- telegram_id
- username
- balance
- wins

Games:
- id
- status
- room
- entry_fee
- prize_pool

Players:
- id
- user_id
- game_id
- card_number
- card_data (JSON)

Transactions:
- id
- user_id
- amount
- status
- tx_ref

---

8. REDIS (REAL-TIME STATE)

Store:
- active game state
- card availability (1–600)
- called numbers
- timers

Use Redis Pub/Sub for broadcasting updates

---

9. PAYMENT INTEGRATION (Telegram Bot)

- All payments (deposits / withdrawals) are handled informally via the Telegram Bot (Telebirr)
- Support transaction history tracking

---

10. FRONTEND PAGES (Next.js)

- Home (menu)
- Stake selection
- Card selection
- Game screen
- Winner screen

Use:
- Tailwind for UI
- Zustand or Context API for state
- WebSocket client for live updates

---

11. GAME UI FEATURES

- Bingo card (5x5 grid)
- Highlight current number
- Show called numbers history
- Countdown timer
- Prize pool display
- Player count

---

12. LEADERBOARD

- Top players by wins
- Display top 10
- Update after each game

---

13. PROFIT SYSTEM

- Entry fee per player
- Prize pool = total entry fees
- Commission (10–15%)
- Winner gets remaining

---

14. SECURITY

- Validate Telegram initData
- Prevent duplicate card selection
- Prevent cheating

---

15. PROJECT STRUCTURE

/backend
  main.py
  websocket.py
  game_engine.py
  models.py

  redis_client.py

/frontend
  app/
    page.tsx
    game/
    cards/
    stake/
  components/
  lib/websocket.ts

---

16. DEPLOYMENT

- Backend: Render / Railway
- Frontend: Vercel
- Redis: Upstash
- PostgreSQL: Supabase or Neon

---

OUTPUT REQUIREMENTS:

- Full working backend (FastAPI)
- Full frontend (Next.js)
- WebSocket implementation
- Redis integration
- Telegram bot payment confirmation (informal)
- Clean, commented, production-ready code

Also explain:
- how to run backend
- how to run frontend
- how to connect Telegram Mini App


<!-- use this 10 points for all prooject -->
1.Move all active game state entirely into Redis; use PostgreSQL only for durable records.
2.Broadcast only incremental WebSocket events (never the full game state).
3.Virtualize the 600-card grid on the frontend and memoize individual card components.
4.Let clients run countdown timers locally after receiving a synchronized start time.
5.Store card ownership in Redis Sets or Hashes for constant-time availability checks.
6.Use Redis Sorted Sets for the leaderboard.
7.Use optimistic UI updates for card selection while confirming through the server.
8.Scale FastAPI horizontally behind a load balancer, with Redis Pub/Sub synchronizing all instances.
9. Add background workers (e.g., Celery or Dramatiq with Redis) for non-real-time tasks such as transaction logging, notifications, and game cleanup.
10.Add monitoring (Prometheus/Grafana or similar) and stress-test the system with tools like Locust or k6 before production.
# 🧪 AMHABINGO Testing Guide

## Overview
This guide will help you test the complete AMHABINGO application end-to-end.

---

## Prerequisites

### 1. Backend Running
```bash
cd backend
# Make sure PostgreSQL and Redis are running via Docker
docker-compose up -d

# Start FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend should be available at: http://localhost:8000

### 2. Frontend Running
```bash
cd frontend
npm run dev
```

Frontend should be available at: http://localhost:3000

### 3. Environment Variables

**Backend** (.env):
```env
DATABASE_URL=postgresql+asyncpg://bingo:bingo123@localhost:5432/bingo
REDIS_URL=redis://localhost:6379
CHAPA_SECRET_KEY=your_chapa_key
TELEGRAM_BOT_TOKEN=your_bot_token
```

**Frontend** (.env.local):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## Testing Flow

### Phase 1: Backend API Testing

#### 1.1 Health Check
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"healthy"}`

#### 1.2 Create User
```bash
curl -X POST http://localhost:8000/api/users/ \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_id": 123456789,
    "username": "testuser",
    "first_name": "Test"
  }'
```

#### 1.3 Get Active Games
```bash
curl http://localhost:8000/api/games/active
```

#### 1.4 Create Game (Admin)
```bash
curl -X POST http://localhost:8000/api/games/ \
  -H "Content-Type: application/json" \
  -d '{
    "room": "beginner",
    "entry_fee": 10.0
  }'
```

---

### Phase 2: Frontend Testing

#### 2.1 Home Page
1. Open http://localhost:3000
2. Should see:
   - AMHABINGO logo/title
   - "Play Bingo" button
   - "How to Play" button
   - Balance display
   - Leaderboard button

#### 2.2 Stake Selection
1. Click "Play Bingo"
2. Should see 3 stake options:
   - Beginner (10 ETB)
   - Pro (50 ETB)
   - VIP (100 ETB)
3. Click any stake
4. Should navigate to card selection

#### 2.3 Card Selection (1-600)
1. Should see 600 cards in grid
2. Card states:
   - Purple = Available
   - Green = Your selection
   - Red = Taken by others
3. Click a card to select
4. Should see:
   - Card turns green
   - "Proceed to Payment" button appears
   - Timer starts (60 seconds)
5. Try clicking another card
   - Previous selection should deselect
   - New card should turn green

#### 2.4 Payment Flow
1. Click "Proceed to Payment"
2. Should redirect to Chapa payment page
3. Complete payment (or use test mode)
4. Should redirect back to game page

#### 2.5 Game Screen
1. Should see:
   - Game ID and status
   - Prize pool
   - Player count
   - Your card number
   - 5x5 Bingo card with BINGO header
   - Called numbers section
   - Timer (if in countdown)
   - Audio toggle button
   - Claim Win button

2. Wait for game to start
3. Should see:
   - Status changes: waiting → countdown → active
   - Timer counts down
   - Numbers start being called
   - Current number highlighted in green
   - Previous numbers turn red
   - Numbers auto-marked on your card
   - Audio announcements (if enabled)

#### 2.6 Winner Detection
1. When someone wins:
   - Winner modal appears
   - Shows winner details
   - Shows prize amount
   - Audio announces "Bingo!"
2. Click "Back to Home"
3. Should return to home page

---

### Phase 3: WebSocket Testing

#### 3.1 Open Browser Console
```javascript
// Check WebSocket connection
console.log('WebSocket connected:', window.ws?.readyState === 1);
```

#### 3.2 Monitor Events
Open DevTools → Network → WS tab
Should see messages:
- `card_selected` - When cards are selected
- `timer_update` - Every second during countdown
- `game_started` - When game begins
- `number_called` - Every 3-5 seconds
- `player_won` - When someone wins

---

### Phase 4: Multi-Player Testing

#### 4.1 Open Multiple Tabs
1. Open 3-4 browser tabs
2. Each tab = different player
3. All select different cards
4. Watch real-time updates:
   - Cards turn red when others select
   - Player count increases
   - All see same called numbers
   - All see winner announcement

#### 4.2 Test Card Locking
1. Player 1 selects card #100
2. Player 2 tries to select card #100
3. Should see error or card already red

---

### Phase 5: Audio Testing

#### 5.1 Enable Audio
1. Click speaker icon (🔊)
2. Should hear announcements:
   - "Game starting! Good luck!"
   - "B 5", "I 22", "N 37", etc.
   - "Bingo! We have a winner!"

#### 5.2 Disable Audio
1. Click speaker icon (🔇)
2. Should stop announcements
3. Game continues silently

---

### Phase 6: Edge Cases

#### 6.1 Disconnection
1. Stop backend server
2. Frontend should show "Disconnected - Reconnecting..."
3. Restart backend
4. Should auto-reconnect

#### 6.2 Page Refresh
1. During game, refresh page
2. Should:
   - Reconnect to WebSocket
   - Restore game state
   - Continue playing

#### 6.3 Multiple Winners
1. Manually trigger multiple wins (backend)
2. Should show all winners in modal
3. Prize split equally

#### 6.4 Timer Expiry
1. Select card
2. Wait 60 seconds without paying
3. Card should be released
4. Others can select it

---

## Expected Behaviors

### ✅ Correct Behaviors
- Cards update in real-time
- Numbers auto-marked on card
- Audio announces numbers
- Winner detected immediately
- Prize calculated correctly
- WebSocket reconnects automatically
- Haptic feedback on mobile
- Smooth animations

### ❌ Incorrect Behaviors
- Cards not updating
- Numbers not being marked
- Audio not working
- Winner not detected
- WebSocket not connecting
- Payment not verifying
- Timer not counting down

---

## Debugging Tips

### Backend Issues
```bash
# Check logs
docker-compose logs -f

# Check Redis
redis-cli
> KEYS *
> GET game:GAME-12345678:state

# Check PostgreSQL
psql -U bingo -d bingo
SELECT * FROM games;
SELECT * FROM players;
```

### Frontend Issues
```javascript
// Check state
import { useGameStore } from '@/store/gameStore';
const state = useGameStore.getState();
console.log('Current game:', state.currentGame);
console.log('Current player:', state.currentPlayer);
console.log('Called numbers:', state.calledNumbers);

// Check WebSocket
console.log('WS connected:', window.ws?.readyState === 1);
```

### Network Issues
1. Open DevTools → Network tab
2. Check API calls (XHR)
3. Check WebSocket (WS)
4. Look for errors (red)

---

## Performance Testing

### Load Testing
```bash
# Install artillery
npm install -g artillery

# Create test script (artillery.yml)
config:
  target: 'http://localhost:8000'
  phases:
    - duration: 60
      arrivalRate: 10

scenarios:
  - name: "Join game"
    flow:
      - post:
          url: "/api/games/join"
          json:
            game_id: "GAME-12345678"
            user_id: 1
            card_number: 100

# Run test
artillery run artillery.yml
```

---

## Mobile Testing (Telegram)

### 1. Setup Telegram Bot
1. Create bot with @BotFather
2. Get bot token
3. Set webhook or use polling

### 2. Create Mini App
1. Go to @BotFather
2. `/newapp`
3. Set URL: https://your-domain.com
4. Upload icon

### 3. Test in Telegram
1. Open bot
2. Click "Play Bingo"
3. Should open Mini App
4. Test all features

---

## Automated Testing (Future)

### Unit Tests
```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### E2E Tests
```bash
# Using Playwright
cd frontend
npx playwright test
```

---

## Checklist

### Backend ✅
- [ ] Server starts without errors
- [ ] Database connected
- [ ] Redis connected
- [ ] API endpoints working
- [ ] WebSocket working
- [ ] Game engine working
- [ ] Payment integration working

### Frontend ✅
- [ ] Home page loads
- [ ] Stake selection works
- [ ] Card selection works (1-600)
- [ ] Real-time updates work
- [ ] Game page displays correctly
- [ ] Bingo card renders
- [ ] Numbers auto-marked
- [ ] Audio works
- [ ] Winner modal appears
- [ ] Navigation works

### Integration ✅
- [ ] Frontend connects to backend
- [ ] WebSocket connects
- [ ] Real-time updates work
- [ ] Multiple players work
- [ ] Payment flow works
- [ ] Winner detection works
- [ ] Prize distribution works

---

## Common Issues & Solutions

### Issue: WebSocket not connecting
**Solution**: Check NEXT_PUBLIC_WS_URL in .env.local

### Issue: Cards not updating
**Solution**: Check Redis connection and WebSocket events

### Issue: Audio not working
**Solution**: Enable audio in browser, check Web Speech API support

### Issue: Payment failing
**Solution**: Check Chapa API key and test mode

### Issue: Numbers not being called
**Solution**: Check game_loop.py is running

---

## Next Steps

1. ✅ Complete basic testing
2. ✅ Fix any bugs found
3. ⏳ Add balance page
4. ⏳ Add leaderboard page
5. ⏳ Add game history
6. ⏳ Deploy to production
7. ⏳ Setup Telegram bot
8. ⏳ Launch! 🚀

---

**Happy Testing! 🎉**

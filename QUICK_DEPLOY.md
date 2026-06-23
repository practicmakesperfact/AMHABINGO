# 🚀 Quick Deploy Guide - Free Tier

Complete deployment in **~20 minutes** using free tiers.

## ✅ Prerequisites Checklist
- [ ] GitHub account
- [ ] Git installed locally
- [ ] Code pushed to GitHub repo

## 📋 Step-by-Step (Copy-Paste Ready)

### 1️⃣ Neon Database (2 min)
```bash
# Go to: https://neon.tech
# 1. Sign up with GitHub
# 2. Create project: "amhabingo"
# 3. Copy connection string (format below)
```
**Connection String Format:**
```
postgresql+asyncpg://user:password@ep-xxx.neon.tech/neondb?sslmode=require
```
📋 Save this - you'll need it for Render.

---

### 2️⃣ Upstash Redis (2 min)
```bash
# Go to: https://console.upstash.com
# 1. Sign up
# 2. Create Database
#    - Name: amhabingo-redis
#    - Type: Regional
#    - Region: AWS US-West (match Render region)
# 3. Copy connection string
```
**Connection String Format:**
```
redis://default:password@us1-xxx.upstash.io:6379
```
📋 Save this - you'll need it for Render.

---

### 3️⃣ Render Backend (5 min)
```bash
# Go to: https://dashboard.render.com
# 1. Sign up with GitHub
# 2. New + → Web Service
# 3. Connect your GitHub repo
# 4. Configure:
```

**Render Configuration:**
- **Name:** `amhabingo-backend`
- **Region:** Oregon
- **Root Directory:** `backend`
- **Runtime:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Plan:** Free

**Environment Variables** (Add these):
```env
DATABASE_URL=<paste-neon-url-here>
REDIS_URL=<paste-upstash-url-here>
BOT_TOKEN=<get-from-botfather-step-5>
TELEGRAM_BOT_SECRET=any_random_secret_string

SECRET_KEY=long_random_string_min_32_chars
COMMISSION_PERCENT=20.0
GAME_INTERVAL_SECONDS=1
COUNTDOWN_SECONDS=60
FRONTEND_URL=https://amhabingo.vercel.app
```

Click **"Create Web Service"** → Wait 3-5 min

📋 **Save your Render URL:** `https://amhabingo-backend.onrender.com`

---

### 4️⃣ Vercel Frontend (3 min)
```bash
# Go to: https://vercel.com
# 1. Sign up with GitHub
# 2. New Project → Import from GitHub
# 3. Select your repository
# 4. Configure:
```

**Vercel Configuration:**
- **Framework Preset:** Next.js (auto-detected)
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`

**Environment Variables** (Add these):
```env
NEXT_PUBLIC_API_URL=<your-render-url>
NEXT_PUBLIC_WS_URL=<your-render-url-with-wss>
```

Example:
```env
NEXT_PUBLIC_API_URL=https://amhabingo-backend.onrender.com
NEXT_PUBLIC_WS_URL=wss://amhabingo-backend.onrender.com
```

Click **"Deploy"** → Wait 2-3 min

📋 **Save your Vercel URL:** `https://amhabingo.vercel.app`

---

### 5️⃣ Telegram Bot Setup (5 min)

**Create Bot:**
```
1. Open Telegram
2. Search: @BotFather
3. Send: /newbot
4. Follow prompts
5. Save token
```

**Create Mini App:**
```
1. Send to @BotFather: /newapp
2. Select your bot
3. Title: AMHABINGO
4. Description: Play Bingo, win real money!
5. Photo: 640x360 image
6. Short name: amhabingo (unique)
7. Web App URL: <your-vercel-url>
```

**Set Commands:**
```
1. Send to @BotFather: /setcommands
2. Paste:
start - Start playing
play - Join game
balance - Check balance
help - Get help
```

**Update Render ENV:**
Go back to Render → Environment → Add:
```
BOT_TOKEN=<your-bot-token>
```
Save changes (triggers redeploy).

---

### 6️⃣ Initialize Database (3 min)

**Option A: Via Render Shell**
```bash
# In Render Dashboard → Shell tab:
cd backend
python init_db.py
python init_cartelas.py
python init_stakes.py
```

**Option B: Via Local (if you have the connection string)**
```bash
cd backend
pip install -r requirements.txt
export DATABASE_URL="<neon-connection-string>"
python init_db.py
python init_cartelas.py
python init_stakes.py
```

---

## ✅ Verify Deployment

### 1. Check Backend
```bash
curl https://amhabingo-backend.onrender.com/health
# Expected: {"status":"ok"}
```

### 2. Check Frontend
Open: `https://amhabingo.vercel.app`
- Should load without errors
- Open browser console (F12) - no errors

### 3. Check Telegram
1. Open your bot in Telegram
2. Send `/start`
3. Click "Play" button
4. Should open your web app

---

## 🎯 Free Tier Limits

| Service | Free Tier | Limits |
|---------|-----------|--------|
| **Neon** | 0.5GB storage | 100 compute hours/month |
| **Upstash** | 10K commands/day | 256MB storage |
| **Render** | 750 hours/month | Sleeps after 15min inactivity |
| **Vercel** | Unlimited | 100GB bandwidth/month |

**Note:** Backend sleeps = first request takes ~30s to wake up.

---

## 🔧 Troubleshooting

**Backend won't start:**
```bash
# Check Render logs:
# Dashboard → Logs tab
# Look for error messages
```

**Database connection error:**
```bash
# Verify DATABASE_URL format:
postgresql+asyncpg://user:pass@host/db?sslmode=require
#                  ↑ Must have this!
```

**Frontend can't reach backend:**
```bash
# Check NEXT_PUBLIC_API_URL in Vercel
# Must match your Render URL exactly
# Redeploy after changing env vars
```

**WebSocket not connecting:**
```bash
# Ensure NEXT_PUBLIC_WS_URL uses wss:// not ws://
wss://amhabingo-backend.onrender.com  ✅
ws://amhabingo-backend.onrender.com   ❌
```

---

## 📊 Post-Deployment

### Monitor Free Tier Usage
- **Neon:** Dashboard → Usage
- **Upstash:** Dashboard → Metrics
- **Render:** Dashboard → Metrics
- **Vercel:** Dashboard → Analytics

### When to Upgrade
- **Neon:** Exceeding 100 compute hours → $19/mo
- **Render:** Need always-on backend → $7/mo
- **Upstash:** Exceeding 10K commands → $10/mo
- **Vercel:** Need more bandwidth → $20/mo

---

## 🎉 You're Live!

**Total Time:** ~20 minutes  
**Total Cost:** $0/month  
**Can handle:** ~100 concurrent users (free tier)

Share your bot with friends and start playing! 🎮

For detailed info, see: `DEPLOYMENT_GUIDE.md`

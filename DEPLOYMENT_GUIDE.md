# 🚀 AMHABINGO Deployment Guide

## Overview
This guide covers deploying AMHABINGO to production using modern cloud platforms.

---

## Architecture

```
┌─────────────────┐
│  Telegram Bot   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Frontend       │◄────►│  Backend     │
│  (Vercel)       │      │  (Render)    │
└─────────────────┘      └──────┬───────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            ┌───────────────┐      ┌──────────────┐
            │  PostgreSQL   │      │    Redis     │
            │  (Neon)       │      │  (Upstash)   │
            └───────────────┘      └──────────────┘
```

---

## Prerequisites

- GitHub account
- Vercel account (frontend)
- Render account (backend)
- Neon account (PostgreSQL database)
- Upstash account (Redis)
- Telegram Bot Token

---

## Step 1: Database Setup (Neon)

### 1.1 Create Project
1. Go to https://neon.tech
2. Click "Sign Up" (use GitHub for easy access)
3. Click "Create Project"
4. Project name: `amhabingo`
5. Database name: `bingo` (or keep default)
6. Region: Choose closest to your users (AWS regions available)
7. PostgreSQL version: 16 (latest)
8. Click "Create Project"

### 1.2 Get Connection String
1. On project dashboard, you'll see connection details
2. Copy the connection string (looks like):
   ```
   postgresql://[user]:[password]@[endpoint].neon.tech/[dbname]?sslmode=require
   ```
3. **Important for asyncpg:** Use this format:
   ```
   postgresql+asyncpg://[user]:[password]@[endpoint].neon.tech/[dbname]?sslmode=require
   ```

### 1.3 Configure Database
Neon automatically includes:
- ✅ Connection pooling (built-in)
- ✅ SSL enabled by default
- ✅ Auto-scaling storage
- ✅ Automatic backups

### 1.4 Run Migrations
```bash
# Install psql if needed
# On Windows: Download from PostgreSQL website or use WSL
# On Mac: brew install postgresql
# On Linux: sudo apt install postgresql-client

# Connect to database (use connection string from Neon dashboard)
psql "postgresql://[user]:[password]@[endpoint].neon.tech/[dbname]?sslmode=require"

# Or run migrations from your app
# Neon works great with Alembic
```

---

## Step 2: Redis Setup (Upstash)

### 2.1 Create Database
1. Go to https://console.upstash.com
2. Click "Create Database"
3. Name: `amhabingo-redis`
4. Type: **Regional** (for better latency)
5. Region: Choose closest to your Render backend
6. Primary Region: AWS (matches Neon)
7. TLS: Enabled (default)
8. Click "Create"

### 2.2 Get Connection URL
1. Go to database details
2. Copy the connection string in format:
   ```
   redis://default:[PASSWORD]@[REGION].upstash.io:6379
   ```
3. Or use REST API URL for serverless:
   ```
   https://[REGION].upstash.io
   ```

---

## Step 3: Backend Deployment (Render)

### 3.1 Prepare Repository
```bash
# Make sure code is pushed to GitHub
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 3.2 Create render.yaml (Optional but Recommended)
Create `render.yaml` in root directory:

```yaml
services:
  - type: web
    name: amhabingo-backend
    env: python
    region: oregon
    plan: free
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: DATABASE_URL
        sync: false
      - key: REDIS_URL
        sync: false
      - key: BOT_TOKEN
        sync: false
      - key: TELEGRAM_BOT_SECRET
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: FRONTEND_URL
        value: https://amhabingo.vercel.app
      - key: COMMISSION_PERCENT
        value: 20.0
      - key: GAME_INTERVAL_SECONDS
        value: 1
      - key: COUNTDOWN_SECONDS
        value: 60
```

### 3.3 Deploy to Render
1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name:** `amhabingo-backend`
   - **Region:** Oregon (or closest to you)
   - **Branch:** `main`
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Plan:** Free (or Starter for better performance)

### 3.4 Configure Environment Variables
In Render dashboard, add these environment variables:

```env
# Database (from Neon)
DATABASE_URL=postgresql+asyncpg://[user]:[password]@[endpoint].neon.tech/[dbname]?sslmode=require

# Redis (from Upstash)
REDIS_URL=redis://default:[PASSWORD]@[REGION].upstash.io:6379


# Telegram
BOT_TOKEN=your_bot_token
TELEGRAM_BOT_SECRET=your_telegram_secret

# App Settings
SECRET_KEY=your_random_secret_key_here_min_32_chars
COMMISSION_PERCENT=20.0
GAME_INTERVAL_SECONDS=1
COUNTDOWN_SECONDS=60

# CORS
FRONTEND_URL=https://amhabingo.vercel.app
```

### 3.5 Deploy
1. Click "Create Web Service"
2. Wait for build (~3-5 minutes)
3. Get deployment URL: `https://amhabingo-backend.onrender.com`

**Note:** Free tier sleeps after 15 minutes of inactivity. First request takes ~30s to wake up.

---

## Step 4: Frontend Deployment (Vercel)

### 4.1 Prepare Frontend
```bash
cd frontend

# Create production .env
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=https://amhabingo-production.up.railway.app
NEXT_PUBLIC_WS_URL=wss://amhabingo-production.up.railway.app
EOF
```

### 4.2 Deploy to Vercel
```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

Or use Vercel Dashboard:
1. Go to https://vercel.com
2. Click "New Project"
3. Import from GitHub
4. Select repository
5. Configure:
   - **Framework Preset:** Next.js
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build` (auto-detected)
   - **Output Directory:** `.next` (auto-detected)
6. Add environment variables:
   ```
   NEXT_PUBLIC_API_URL=https://amhabingo-backend.onrender.com
   NEXT_PUBLIC_WS_URL=wss://amhabingo-backend.onrender.com
   ```
7. Click "Deploy"

### 4.3 Get Deployment URL
- Should be: `https://amhabingo.vercel.app`

---

## Step 5: Telegram Bot Setup

### 5.1 Create Bot
```bash
# Talk to @BotFather on Telegram
/newbot
# Follow prompts
# Save bot token
```

### 5.2 Create Mini App
```bash
# Talk to @BotFather
/newapp
# Select your bot
# Name: AMHABINGO
# Description: Play Bingo and win real money!
# Photo: Upload 640x360 image
# Demo GIF: Optional
# URL: https://amhabingo.vercel.app
```

### 5.3 Set Bot Commands
```bash
# Talk to @BotFather
/setcommands
# Select your bot
# Paste:
start - Start the bot
play - Play Bingo
balance - Check balance
leaderboard - View top players
help - Get help
```

### 5.4 Set Menu Button
```bash
# Talk to @BotFather
/setmenubutton
# Select your bot
# Text: Play Bingo 🎮
# URL: https://amhabingo.vercel.app
```

---

## Step 6: Domain Setup (Optional)

### 6.1 Buy Domain
- Namecheap, GoDaddy, etc.
- Example: `amhabingo.com`

### 6.2 Configure DNS
**For Frontend (Vercel):**
1. Go to Vercel → Project → Settings → Domains
2. Add custom domain
3. Follow DNS instructions

**For Backend (Render):**
1. Go to Render → Service → Settings → Custom Domains
2. Add custom domain (e.g., `api.amhabingo.com`)
3. Update DNS:
   ```
   Type: CNAME
   Name: api
   Value: [your-service].onrender.com
   ```

### 6.3 Update URLs
Update all environment variables with new domains:
- Frontend: `https://amhabingo.com`
- Backend: `https://api.amhabingo.com`

---

## Step 7: SSL/HTTPS

### 7.1 Vercel
- Automatic SSL (Let's Encrypt)
- No configuration needed

### 7.2 Render
- Automatic SSL (Let's Encrypt)
- No configuration needed

---

## Step 8: Monitoring & Logging

### 8.1 Render Logs
1. Go to Render Dashboard
2. Select your service
3. Click "Logs" tab (real-time logs)
4. Or use CLI:
```bash
# Install Render CLI (optional)
# brew install render (Mac) or download from render.com/docs/cli

# View logs
render logs
```

### 8.2 Vercel Logs
1. Go to Vercel Dashboard
2. Select project
3. Click "Logs" tab

### 8.3 Error Tracking (Optional)
**Sentry:**
```bash
# Install
npm install @sentry/nextjs @sentry/python

# Configure
# Follow Sentry docs
```

---

## Step 9: Testing Production

### 9.1 Health Check
```bash
curl https://api.amhabingo.com/health
```

### 9.2 Frontend Check
1. Open https://amhabingo.com
2. Test all features
3. Check browser console for errors

### 9.3 Telegram Check
1. Open bot in Telegram
2. Click "Play Bingo"
3. Test complete flow

---

## Scaling Considerations

### Database
- Neon auto-scales storage (free tier: 0.5GB, scales to 3GB)
- Built-in connection pooling
- Free tier has 100 hours compute/month
- Upgrade to Pro for unlimited compute ($19/month)

### Redis
- Upstash auto-scales
- Monitor memory usage
- Upgrade plan if needed

### Backend
- Render Free tier: 512MB RAM, 0.1 CPU (sleeps after 15 min inactivity)
- Upgrade to Starter ($7/month) or higher for always-on
- Auto-scales on paid tiers
- Monitor from dashboard

### Frontend
- Vercel auto-scales
- CDN caching
- No action needed

---

## Backup Strategy

### Database Backups
```bash
# Neon provides automatic backups (point-in-time recovery on paid plans)
# Free tier: Daily backups kept for 7 days
# Manual backup:
pg_dump "postgresql://[user]:[password]@[endpoint].neon.tech/[dbname]?sslmode=require" > backup.sql
```

### Redis Backups
- Upstash has automatic snapshots
- Export data periodically

---

## Security Checklist

- [ ] HTTPS enabled everywhere
- [ ] Environment variables secured
- [ ] Database password strong
- [ ] API keys rotated regularly
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection

---

## Cost Estimation

### Free Tier (Development & Early Production)
- **Vercel:** Free (100GB bandwidth, unlimited deployments)
- **Render:** Free (750 hours/month, sleeps after inactivity)
- **Neon:** Free (0.5GB storage, 100 compute hours/month)
- **Upstash:** Free (10K commands/day)
- **Total: $0/month** ✅

**Limitations:**
- Backend sleeps after 15 min (30s wake time)
- Database has 100 compute hours/month limit
- Redis 10K daily commands

### Production (1000 active users)
- **Vercel:** Free - $20/month (Pro if you need more bandwidth)
- **Render:** $7/month (Starter - always on, 512MB RAM)
- **Neon:** $19/month (Pro - unlimited compute, 10GB storage)
- **Upstash:** Free or $10/month (if exceeding limits)
- **Total: ~$26-56/month**

### Scale (10,000+ users)
- **Vercel:** $20/month (Pro)
- **Render:** $25-85/month (Standard or Pro instance)
- **Neon:** $69/month (Scale - high performance, 50GB)
- **Upstash:** $30/month
- **Total: ~$144-204/month**

---

## Maintenance

### Daily
- Check error logs
- Monitor uptime
- Check payment processing

### Weekly
- Review performance metrics
- Check database size
- Update dependencies

### Monthly
- Security updates
- Backup verification
- Cost optimization

---

## Rollback Plan

### Backend Rollback
```bash
# Render
# Go to Dashboard → Deploy → Select previous successful deploy → "Rollback to this version"
# Or redeploy from specific commit
```

### Frontend Rollback
```bash
# Vercel
vercel rollback
```

### Database Rollback
```bash
# Restore from backup
psql "postgresql://..." < backup.sql
```

---

## Support & Troubleshooting

### Common Issues

**Issue: WebSocket not connecting**
- Check WSS (not WS) in production
- Verify CORS settings in backend
- Check Render logs for connection errors
- Render supports WebSockets on all plans


**Issue: Database connection errors**
- Check connection string format (must include `?sslmode=require`)
- Neon requires SSL connections
- Use `postgresql+asyncpg://` for async connections
- Check compute hours limit on free tier

---

## Launch Checklist

- [ ] Backend deployed and healthy
- [ ] Frontend deployed and accessible
- [ ] Database migrated
- [ ] Redis connected
- [ ] Telegram bot configured
- [ ] Informal payment via Telegram bot tested
- [ ] SSL certificates active
- [ ] Monitoring setup
- [ ] Backups configured
- [ ] Documentation complete
- [ ] Team trained
- [ ] Support channels ready

---

## Post-Launch

1. Monitor first 24 hours closely
2. Gather user feedback
3. Fix critical bugs immediately
4. Plan feature updates
5. Scale as needed

---

**Ready to launch! 🚀**

For support: [your-email@example.com]

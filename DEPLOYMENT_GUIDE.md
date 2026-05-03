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
│  (Vercel)       │      │  (Railway)   │
└─────────────────┘      └──────┬───────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
            ┌───────────────┐      ┌──────────────┐
            │  PostgreSQL   │      │    Redis     │
            │  (Supabase)   │      │  (Upstash)   │
            └───────────────┘      └──────────────┘
```

---

## Prerequisites

- GitHub account
- Vercel account
- Railway account (or Render)
- Supabase account
- Upstash account
- Chapa account (payment)
- Telegram Bot Token

---

## Step 1: Database Setup (Supabase)

### 1.1 Create Project
1. Go to https://supabase.com
2. Click "New Project"
3. Choose organization
4. Set project name: `amhabingo`
5. Set database password (save it!)
6. Choose region (closest to users)
7. Wait for provisioning (~2 minutes)

### 1.2 Get Connection String
1. Go to Project Settings → Database
2. Copy "Connection string" (URI mode)
3. Replace `[YOUR-PASSWORD]` with your password
4. Should look like:
   ```
   postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

### 1.3 Run Migrations
```bash
# Install psql if needed
# On Windows: Download from PostgreSQL website
# On Mac: brew install postgresql
# On Linux: sudo apt install postgresql-client

# Connect to database
psql "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

# Run schema (copy from backend/app/models.py)
# Or use Alembic migrations
```

---

## Step 2: Redis Setup (Upstash)

### 2.1 Create Database
1. Go to https://upstash.com
2. Click "Create Database"
3. Name: `amhabingo-redis`
4. Type: Regional
5. Region: Choose closest to backend
6. Click "Create"

### 2.2 Get Connection URL
1. Go to database details
2. Copy "UPSTASH_REDIS_REST_URL"
3. Should look like:
   ```
   redis://default:[PASSWORD]@[REGION].upstash.io:6379
   ```

---

## Step 3: Backend Deployment (Railway)

### 3.1 Prepare Repository
```bash
# Make sure code is pushed to GitHub
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 3.2 Deploy to Railway
1. Go to https://railway.app
2. Click "New Project"
3. Choose "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Python/FastAPI

### 3.3 Configure Environment Variables
In Railway dashboard, add:

```env
# Database
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# Redis
REDIS_URL=redis://default:[PASSWORD]@[REGION].upstash.io:6379

# Chapa Payment
CHAPA_SECRET_KEY=your_chapa_secret_key
CHAPA_WEBHOOK_SECRET=your_webhook_secret

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token

# App Settings
SECRET_KEY=your_random_secret_key_here
COMMISSION_PERCENT=10
MAX_PLAYERS=50
COUNTDOWN_SECONDS=60

# CORS
FRONTEND_URL=https://your-app.vercel.app
```

### 3.4 Set Root Directory
1. Go to Settings → Deploy
2. Set "Root Directory": `backend`
3. Set "Start Command": `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 3.5 Deploy
1. Click "Deploy"
2. Wait for build (~2-3 minutes)
3. Get deployment URL: `https://amhabingo-production.up.railway.app`

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
5. Set "Root Directory": `frontend`
6. Add environment variables:
   ```
   NEXT_PUBLIC_API_URL=https://amhabingo-production.up.railway.app
   NEXT_PUBLIC_WS_URL=wss://amhabingo-production.up.railway.app
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

## Step 6: Payment Setup (Chapa)

### 6.1 Create Account
1. Go to https://chapa.co
2. Sign up for business account
3. Complete KYC verification

### 6.2 Get API Keys
1. Go to Dashboard → Settings → API Keys
2. Copy "Secret Key"
3. Add to Railway environment variables

### 6.3 Set Webhook
1. Go to Dashboard → Settings → Webhooks
2. Add webhook URL:
   ```
   https://amhabingo-production.up.railway.app/api/payments/webhook
   ```
3. Copy webhook secret
4. Add to Railway environment variables

---

## Step 7: Domain Setup (Optional)

### 7.1 Buy Domain
- Namecheap, GoDaddy, etc.
- Example: `amhabingo.com`

### 7.2 Configure DNS
**For Frontend (Vercel):**
1. Go to Vercel → Project → Settings → Domains
2. Add custom domain
3. Follow DNS instructions

**For Backend (Railway):**
1. Go to Railway → Project → Settings → Domains
2. Add custom domain
3. Update DNS:
   ```
   Type: CNAME
   Name: api
   Value: [railway-domain]
   ```

### 7.3 Update URLs
Update all environment variables with new domains:
- Frontend: `https://amhabingo.com`
- Backend: `https://api.amhabingo.com`

---

## Step 8: SSL/HTTPS

### 8.1 Vercel
- Automatic SSL (Let's Encrypt)
- No configuration needed

### 8.2 Railway
- Automatic SSL
- No configuration needed

---

## Step 9: Monitoring & Logging

### 9.1 Railway Logs
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# View logs
railway logs
```

### 9.2 Vercel Logs
1. Go to Vercel Dashboard
2. Select project
3. Click "Logs" tab

### 9.3 Error Tracking (Optional)
**Sentry:**
```bash
# Install
npm install @sentry/nextjs @sentry/python

# Configure
# Follow Sentry docs
```

---

## Step 10: Testing Production

### 10.1 Health Check
```bash
curl https://api.amhabingo.com/health
```

### 10.2 Frontend Check
1. Open https://amhabingo.com
2. Test all features
3. Check browser console for errors

### 10.3 Telegram Check
1. Open bot in Telegram
2. Click "Play Bingo"
3. Test complete flow

---

## Scaling Considerations

### Database
- Supabase auto-scales
- Monitor connection pool
- Add read replicas if needed

### Redis
- Upstash auto-scales
- Monitor memory usage
- Upgrade plan if needed

### Backend
- Railway auto-scales
- Monitor CPU/memory
- Add more instances if needed

### Frontend
- Vercel auto-scales
- CDN caching
- No action needed

---

## Backup Strategy

### Database Backups
```bash
# Supabase has automatic backups
# Manual backup:
pg_dump "postgresql://..." > backup.sql
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

### Free Tier (Development)
- Vercel: Free
- Railway: $5/month (500 hours)
- Supabase: Free (500MB)
- Upstash: Free (10K commands/day)
- **Total: ~$5/month**

### Production (1000 users)
- Vercel: Free - $20/month
- Railway: $20/month
- Supabase: $25/month
- Upstash: $10/month
- **Total: ~$55-75/month**

### Scale (10,000 users)
- Vercel: $20/month
- Railway: $50/month
- Supabase: $100/month
- Upstash: $30/month
- **Total: ~$200/month**

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
# Railway
railway rollback
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
- Verify CORS settings
- Check Railway logs

**Issue: Payment failing**
- Verify Chapa API key
- Check webhook URL
- Test in sandbox mode first

**Issue: Database connection errors**
- Check connection string
- Verify IP whitelist (Supabase)
- Check connection pool size

---

## Launch Checklist

- [ ] Backend deployed and healthy
- [ ] Frontend deployed and accessible
- [ ] Database migrated
- [ ] Redis connected
- [ ] Telegram bot configured
- [ ] Payment integration tested
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

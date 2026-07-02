# 🤖 TELEGRAM MINI APP DEPLOYMENT GUIDE

Complete guide to deploy AMHABINGO as a Telegram Mini App

---

## 📋 PREREQUISITES

### 1. **Telegram Bot** (Required)
- Bot Token from @BotFather
- Bot must be created and configured

### 2. **Domain & SSL Certificate** (Required)
- Public domain name (e.g., amhabingo.com)
- Valid SSL certificate (HTTPS required)
- You can use:
  - Paid: Your own domain + Let's Encrypt SSL
  - Free: Vercel, Netlify, Railway (auto HTTPS)

### 3. **Server** (For Backend)
- VPS or cloud server (AWS, DigitalOcean, etc.)
- Or serverless (Railway, Render, Fly.io)

---

## 🚀 STEP-BY-STEP DEPLOYMENT

### STEP 1: Create Telegram Bot

1. **Open Telegram and search for @BotFather**

2. **Create new bot:**
```
/newbot
```

3. **Follow prompts:**
```
Choose a name for your bot: AMHABINGO
Choose a username: amhabingo_bot
```

4. **Save your Bot Token:**
```
1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

5. **Set bot commands:**
```
/setcommands

Select your bot: @amhabingo_bot

Send this list:
start - Start playing Bingo
help - Get help
wallet - Check balance
history - View game history
rules - Game rules
```

---

### STEP 2: Deploy Frontend (Vercel - Recommended)

#### Option A: Deploy to Vercel (Free HTTPS)

1. **Install Vercel CLI:**
```bash
npm install -g vercel
```

2. **Login to Vercel:**
```bash
vercel login
```

3. **Deploy frontend:**
```bash
cd frontend
vercel
```

4. **Follow prompts:**
```
? Set up and deploy "frontend"? Yes
? Which scope? [Your account]
? Link to existing project? No
? What's your project's name? amhabingo
? In which directory is your code located? ./
```

5. **Configure environment variables in Vercel dashboard:**
```env
NEXT_PUBLIC_API_URL=https://your-backend-url.com
NEXT_PUBLIC_WS_URL=wss://your-backend-url.com
```

6. **Get your frontend URL:**
```
https://amhabingo.vercel.app
```

#### Option B: Deploy to Your Own Server

```bash
cd frontend
npm run build
npm start
```

Or use Nginx:
```nginx
server {
    listen 80;
    server_name amhabingo.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

### STEP 3: Deploy Backend

#### Option A: Railway (Easy, Free Tier)

1. **Create account at railway.app**

2. **Install Railway CLI:**
```bash
npm install -g @railway/cli
```

3. **Login:**
```bash
railway login
```

4. **Deploy:**
```bash
cd backend
railway init
railway up
```

5. **Add environment variables in Railway dashboard:**
```env
DATABASE_URL=postgresql://user:pass@host/dbname
REDIS_URL=redis://host:6379
BOT_TOKEN=your_bot_token_here
TELEGRAM_BOT_SECRET=your_secret_here
FRONTEND_URL=https://amhabingo.vercel.app
```

6. **Get your backend URL:**
```
https://amhabingo-production.up.railway.app
```

#### Option B: Your Own VPS

```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip python3-venv nginx

# Setup project
cd /var/www/amhabingo/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo nano /etc/systemd/system/amhabingo.service
```

```ini
[Unit]
Description=AMHABINGO Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/amhabingo/backend
Environment="PATH=/var/www/amhabingo/backend/venv/bin"
ExecStart=/var/www/amhabingo/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl daemon-reload
sudo systemctl start amhabingo
sudo systemctl enable amhabingo
```

---

### STEP 4: Configure Telegram Mini App

1. **Go back to @BotFather**

2. **Set Web App URL:**
```
/newapp

Select your bot: @amhabingo_bot
Title: AMHABINGO
Description: Play Bingo and win real money!
Photo: [Upload your icon]
Demo GIF: [Optional]
Web App URL: https://amhabingo.vercel.app
```

3. **Set Menu Button:**
```
/setmenubutton

Select bot: @amhabingo_bot
Send web app URL: https://amhabingo.vercel.app
Button text: 🎮 Play Now
```

4. **Optional - Add inline mode:**
```
/setinline

Select bot: @amhabingo_bot
Placeholder: Play AMHABINGO
```

---

### STEP 5: Update Frontend for Telegram

Your frontend already has Telegram integration! Just verify these files:

#### `frontend/hooks/useTelegram.ts`
```typescript
export const useTelegram = () => {
  const tg = typeof window !== 'undefined' 
    ? (window as any).Telegram?.WebApp 
    : null;

  useEffect(() => {
    if (tg) {
      tg.ready();
      tg.expand();
    }
  }, [tg]);

  return {
    tg,
    user: tg?.initDataUnsafe?.user,
    initData: tg?.initData,
  };
};
```

#### Update `frontend/app/layout.tsx` to include Telegram script:
```tsx
<Script 
  src="https://telegram.org/js/telegram-web-app.js"
  strategy="beforeInteractive"
/>
```

---

### STEP 6: Test Your Mini App

1. **Open your bot in Telegram:**
```
https://t.me/amhabingo_bot
```

2. **Click "Play Now" button or send `/start`**

3. **The Mini App should open inside Telegram!**

---

## 🔧 ENVIRONMENT VARIABLES

### Backend `.env`
```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./bingo.db
# For production, use PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname

# Redis
REDIS_URL=redis://localhost:6379

# Telegram
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_BOT_SECRET=your_webhook_secret_here

# App Config
SECRET_KEY=change-this-to-random-string-in-production
COMMISSION_PERCENT=20.0
GAME_INTERVAL_SECONDS=5
COUNTDOWN_SECONDS=60

# CORS
FRONTEND_URL=https://amhabingo.vercel.app
```

### Frontend `.env.local`
```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_WS_URL=wss://your-backend.railway.app
```

---

## 📱 BOT COMMANDS SETUP

Set these commands in @BotFather using `/setcommands`:

```
start - 🎮 Start playing Bingo
play - 🎯 Join a game
wallet - 💰 Check your balance
deposit - 💳 Add money to wallet
withdraw - 🏦 Withdraw winnings
history - 📊 View game history
rules - 📖 Learn how to play
help - ❓ Get help
support - 🆘 Contact support
```

---

## 🎨 CUSTOMIZATION

### Bot Profile Picture
- Size: 512x512 pixels
- Format: PNG with transparency
- Upload via @BotFather using `/setuserpic`

### About Text
```
/setabouttext

🎮 AMHABINGO - Ethiopian Bingo Game

Play classic 75-ball Bingo and win real money!

🎯 600 unique cartelas
💰 Multiple stake levels (10-100 ETB)
⚡ Fast games (5 min average)
🏆 Win up to 480x your stake!

Start playing now! 🚀
```

### Description
```
/setdescription

Play Ethiopian Bingo online. Win real money prizes. Fast games, fair play, instant withdrawals.
```

---

## 🔒 SECURITY CHECKLIST

### Backend Security:
- ✅ Enable HTTPS (SSL certificate)
- ✅ Validate Telegram initData
- ✅ Use environment variables for secrets
- ✅ Enable rate limiting
- ✅ Secure WebSocket connections (WSS)
- ✅ Validate all user inputs
- ✅ Use prepared statements (prevent SQL injection)

### Frontend Security:
- ✅ Verify Telegram WebApp context
- ✅ Don't expose API keys
- ✅ Validate user actions
- ✅ Use HTTPS only

---

## 🧪 TESTING

### 1. Local Testing (Before Deployment)

```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn app.main:app --reload

# Terminal 2 - Frontend  
cd frontend
npm run dev

# Terminal 3 - ngrok (for Telegram testing)
ngrok http 3000
```

Then use the ngrok URL in @BotFather temporarily.

### 2. Production Testing

After deployment:
1. Open bot in Telegram
2. Test all game flows:
   - Select stake
   - Choose cartela
   - Play game
   - Win/lose scenarios
   - Wallet operations
3. Test on multiple devices:
   - Android
   - iOS
   - Desktop

---



## 📊 MONITORING

### Add Logging

```python
# backend/app/main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Monitor Metrics:
- Active games
- Player count
- Revenue
- Error rates
- Response times

---

## 🚨 COMMON ISSUES

### Issue 1: "Failed to connect to backend"
**Solution:**
- Check CORS settings
- Verify `FRONTEND_URL` in backend `.env`
- Ensure backend is running

### Issue 2: "WebSocket connection failed"
**Solution:**
- Use WSS (secure WebSocket) in production
- Check firewall rules
- Verify WebSocket endpoint is accessible

### Issue 3: "Invalid Telegram data"
**Solution:**
- Verify `BOT_TOKEN` is correct
- Check Telegram script is loaded
- Ensure using HTTPS

### Issue 4: Mini App doesn't open
**Solution:**
- Verify Web App URL in @BotFather
- Check URL is accessible (HTTPS required)
- Try clearing Telegram cache

---

## 📝 DEPLOYMENT CHECKLIST

- [ ] Bot created in @BotFather
- [ ] Bot Token saved securely
- [ ] Frontend deployed with HTTPS
- [ ] Backend deployed with HTTPS
- [ ] Database initialized (`init_db.py`)
- [ ] Cartelas generated (`init_cartelas.py`)
- [ ] Environment variables configured
- [ ] Web App URL set in @BotFather
- [ ] Bot commands configured
- [ ] Bot profile picture uploaded
- [ ] About text and description set
- [ ] Informal payment flow verified
- [ ] Tested on Android
- [ ] Tested on iOS
- [ ] Tested on Desktop
- [ ] Monitoring enabled
- [ ] Backup system configured

---

## 🎉 LAUNCH!

Once everything is deployed and tested:

1. **Announce your bot:**
```
Share: https://t.me/amhabingo_bot
```

2. **Promote:**
   - Ethiopian Telegram groups
   - Social media
   - Gaming communities
   - Friends and family

3. **Monitor:**
   - Check logs for errors
   - Watch player count
   - Monitor revenue
   - Gather feedback

---

## 📞 NEED HELP?

- **Telegram API Docs:** https://core.telegram.org/bots/webapps
- **Vercel Docs:** https://vercel.com/docs
- **Railway Docs:** https://docs.railway.app/

---

**Good luck with your Telegram Mini App! 🚀**

# 🎮 Telegram Bingo Game Bot

A fully functional Telegram bot for playing Bingo games with integrated payment system using Chapa API.

## ✨ Features

- **User Management**: Automatic user registration, balance tracking, game statistics
- **Game System**: Create, join, and play bingo games with multiple players
- **Bingo Cards**: Auto-generated 5x5 cards with FREE center space
- **Game Loop**: Automated number calling every 5 seconds
- **Win Detection**: Automatic checking for rows, columns, and diagonals
- **Payment Integration**: Chapa API for entry fee payments
- **Wallet System**: Track balances and automatic prize distribution
- **Leaderboard**: View top players by balance
- **Security**: Payment verification, duplicate join prevention

## 🛠️ Tech Stack

- Python 3.8+
- python-telegram-bot v20+
- SQLite database
- Chapa Payment API
- asyncio for concurrent game loops

## 📦 Installation

1. **Clone or download the project**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
   - Copy `.env.example` to `.env`
   - Fill in your credentials:
```env
BOT_TOKEN=your_telegram_bot_token_here
CHAPA_SECRET_KEY=your_chapa_secret_key_here
ENTRY_FEE=10
COMMISSION_PERCENT=10
```

4. **Get your Bot Token**:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Use `/newbot` command
   - Copy the token to `.env`

5. **Get Chapa API Key**:
   - Sign up at [Chapa](https://chapa.co)
   - Get your secret key from dashboard
   - Add to `.env`

## 🚀 Running the Bot

```bash
python bot.py
```

The bot will start and listen for commands!

## 📱 Bot Commands

- `/start` - Register and view your profile
- `/create_game` - Create a new bingo game
- `/join_game` - Join an existing game (requires payment)
- `/start_game` - Start the game (minimum 2 players)
- `/my_card` - View your bingo card
- `/balance` - Check your balance
- `/leaderboard` - View top 10 players

## 🎯 How to Play

1. **Create a Game**: Use `/create_game` in a group or private chat
2. **Join**: Players click "Join Game" button and complete payment
3. **Start**: Once 2+ players joined, use `/start_game`
4. **Play**: Bot calls numbers every 5 seconds, cards auto-mark
5. **Win**: First player to complete a row, column, or diagonal wins!

## 💰 Payment Flow

1. Player clicks "Join Game"
2. Bot generates Chapa payment link
3. Player completes payment on Chapa
4. Player clicks "I've Paid - Verify"
5. Bot verifies payment with Chapa API
6. Player receives bingo card and joins game

## 🗄️ Database Schema

### Users Table
- `id`: Primary key
- `telegram_id`: Unique Telegram user ID
- `username`: Telegram username
- `balance`: Current balance in ETB
- `games_played`: Total games played

### Games Table
- `id`: Primary key
- `chat_id`: Telegram chat ID
- `status`: waiting/active/finished
- `entry_fee`: Entry fee amount
- `total_pool`: Total prize pool
- `winner_id`: Winner user ID
- `called_numbers`: JSON array of called numbers

### Players Table
- `id`: Primary key
- `game_id`: Foreign key to games
- `user_id`: Foreign key to users
- `card`: JSON 5x5 bingo card
- `marked`: JSON array of marked positions

### Transactions Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `game_id`: Foreign key to games
- `amount`: Transaction amount
- `tx_ref`: Unique transaction reference
- `status`: pending/success/failed
- `type`: entry_fee/payout

## 🎴 Bingo Card Format

```
  B    I    N    G    O
━━━━━━━━━━━━━━━━━━━━━━━━━━━
 5   18   35   52   67
 12  22   41   48   70
 8   29  FREE  60   73
 14  25   38   55   62
 3   17   44   59   75
```

- Numbers 1-75 distributed across columns
- B: 1-15, I: 16-30, N: 31-45, G: 46-60, O: 61-75
- Center is always FREE
- Marked numbers shown with brackets: [12]

## 🏆 Winning Patterns

- **Row**: Any complete horizontal line
- **Column**: Any complete vertical line
- **Diagonal**: Top-left to bottom-right OR top-right to bottom-left

## 💵 Prize Distribution

- Entry fee collected from all players
- Winner receives: `total_pool × (1 - commission%)`
- Default commission: 10%
- Example: 5 players × 10 ETB = 50 ETB pool → Winner gets 45 ETB

## 🔒 Security Features

- Payment verification before joining
- Duplicate join prevention
- Transaction tracking
- Server-side win validation
- No client-side manipulation possible

## 📁 Project Structure

```
bingo-bot/
├── bot.py           # Main bot logic and handlers
├── game.py          # Bingo game logic (card generation, win checking)
├── payment.py       # Chapa payment integration
├── db.py            # Database operations
├── requirements.txt # Python dependencies
├── .env.example     # Environment variables template
└── README.md        # This file
```

## 🐛 Troubleshooting

**Bot doesn't respond**:
- Check BOT_TOKEN is correct
- Ensure bot is not blocked
- Check internet connection

**Payment fails**:
- Verify CHAPA_SECRET_KEY is correct
- Check Chapa account is active
- Ensure test/production mode matches

**Database errors**:
- Delete `bingo.db` and restart (will reset all data)
- Check file permissions

## 🔄 Future Enhancements

- Multiple game rooms
- Custom entry fees per game
- Pattern variations (X, T, L shapes)
- Tournament mode
- Withdrawal system
- Admin dashboard
- Game history

## 📄 License

This project is open source and available for educational purposes.

## 🤝 Support

For issues or questions:
1. Check this README
2. Review the code comments
3. Test with Chapa sandbox mode first

---

**Happy Gaming! 🎉**

import os
import asyncio
import logging
from typing import Dict
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from db import Database
from game import BingoGame
from payment import ChapaPayment

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAPA_SECRET_KEY = os.getenv("CHAPA_SECRET_KEY")
ENTRY_FEE = float(os.getenv("ENTRY_FEE", "10"))
COMMISSION_PERCENT = float(os.getenv("COMMISSION_PERCENT", "10"))
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

# Initialize services
db = Database()
payment_service = ChapaPayment(CHAPA_SECRET_KEY)

# Active games (game_id -> asyncio.Task)
active_game_tasks: Dict[int, asyncio.Task] = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Create or get user
    db.create_user(user.id, user.username)
    user_data = db.get_user(user.id)
    
    welcome_message = (
        f"🎉 Welcome to Bingo Game Bot, {user.first_name}!\n\n"
        f"💰 Your Balance: {user_data['balance']:.2f} ETB\n"
        f"🎮 Games Played: {user_data['games_played']}\n\n"
        f"Commands:\n"
        f"/create_game - Create a new bingo game\n"
        f"/join_game - Join an existing game\n"
        f"/start_game - Start the game (min 2 players)\n"
        f"/my_card - View your bingo card\n"
        f"/balance - Check your balance\n"
        f"/leaderboard - View top players\n"
    )
    
    await update.message.reply_text(welcome_message)


async def create_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /create_game command"""
    chat_id = update.effective_chat.id
    
    # Check if there's already an active game
    existing_game = db.get_active_game(chat_id)
    if existing_game:
        await update.message.reply_text(
            f"⚠️ There's already an active game (ID: {existing_game['id']})!\n"
            f"Status: {existing_game['status']}\n"
            f"Use /join_game to join or /start_game to start it."
        )
        return
    
    # Create new game
    game_id = db.create_game(chat_id, ENTRY_FEE)
    
    keyboard = [[InlineKeyboardButton("💰 Join Game", callback_data=f"join_{game_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎮 New Bingo Game Created!\n\n"
        f"Game ID: {game_id}\n"
        f"Entry Fee: {ENTRY_FEE} ETB\n"
        f"Minimum Players: 2\n\n"
        f"Click the button below to join!",
        reply_markup=reply_markup
    )


async def join_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /join_game command"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Get active game
    game = db.get_active_game(chat_id)
    if not game:
        await update.message.reply_text("❌ No active game found. Use /create_game to create one!")
        return
    
    if game['status'] != 'waiting':
        await update.message.reply_text("❌ This game has already started!")
        return
    
    # Create join button
    keyboard = [[InlineKeyboardButton("💰 Pay & Join", callback_data=f"join_{game['id']}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎮 Join Game #{game['id']}\n"
        f"Entry Fee: {game['entry_fee']} ETB\n\n"
        f"Click the button to proceed with payment:",
        reply_markup=reply_markup
    )


async def handle_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle join game button callback"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    game_id = int(query.data.split("_")[1])
    
    # Get game
    game = db.get_game(game_id)
    if not game:
        await query.edit_message_text("❌ Game not found!")
        return
    
    if game['status'] != 'waiting':
        await query.edit_message_text("❌ This game has already started!")
        return
    
    # Get user from database
    user_data = db.get_user(user.id)
    if not user_data:
        db.create_user(user.id, user.username)
        user_data = db.get_user(user.id)
    
    # Check if already joined
    existing_player = db.get_player(game_id, user_data['id'])
    if existing_player:
        await query.edit_message_text("✅ You've already joined this game!")
        return
    
    # Generate transaction reference
    tx_ref = payment_service.generate_tx_ref(user_data['id'], game_id)
    
    # Create transaction record
    db.create_transaction(
        user_id=user_data['id'],
        amount=game['entry_fee'],
        tx_ref=tx_ref,
        transaction_type='entry_fee',
        game_id=game_id
    )
    
    # Initialize payment
    # Use a valid email format - Chapa requires real email domains
    user_email = f"bingo.player.{user.id}@gmail.com"
    
    payment_result = await payment_service.initialize_payment(
        amount=game['entry_fee'],
        email=user_email,
        first_name=user.first_name[:20] if user.first_name else "Player",
        last_name=user.last_name[:20] if user.last_name else f"U{user.id}",
        callback_url=f"https://t.me/{context.bot.username}",
        tx_ref=tx_ref
    )
    
    if payment_result.get('status') == 'success':
        checkout_url = payment_result['data']['checkout_url']
        
        keyboard = [
            [InlineKeyboardButton("💳 Pay Now", url=checkout_url)],
            [InlineKeyboardButton("✅ I've Paid - Verify", callback_data=f"verify_{tx_ref}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"💰 Payment Required\n\n"
            f"Amount: {game['entry_fee']} ETB\n"
            f"Transaction: {tx_ref}\n\n"
            f"1. Click 'Pay Now' to complete payment\n"
            f"2. After payment, click 'I've Paid' to verify",
            reply_markup=reply_markup
        )
    else:
        error_msg = payment_result.get('message', 'Unknown error')
        error_data = payment_result.get('data', {})
        
        await query.edit_message_text(
            f"❌ Payment initialization failed!\n\n"
            f"Error: {error_msg}\n"
            f"Details: {error_data}\n\n"
            f"Please contact support or try again later."
        )


async def handle_verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment verification callback"""
    query = update.callback_query
    await query.answer("Verifying payment...")
    
    user = query.from_user
    tx_ref = query.data.split("_", 1)[1]
    
    # Get transaction
    transaction = db.get_transaction(tx_ref)
    if not transaction:
        await query.edit_message_text("❌ Transaction not found!")
        return
    
    if transaction['status'] == 'success':
        await query.edit_message_text("✅ You've already joined this game!")
        return
    
    # Verify payment with Chapa
    verification = await payment_service.verify_payment(tx_ref)
    
    # Debug: Print full verification response
    print(f"Verification Response: {verification}")
    
    # TEST MODE: Auto-approve payments for testing
    if TEST_MODE:
        logger.info(f"TEST MODE: Auto-approving payment for {tx_ref}")
        payment_status = 'success'
    else:
        # Check if verification was successful
        if verification.get('status') != 'success':
            await query.edit_message_text(
                f"❌ Verification failed!\n\n"
                f"Error: {verification.get('message', 'Unknown error')}\n"
                f"Please try again or contact support."
            )
            return
        
        payment_data = verification.get('data', {})
        payment_status = payment_data.get('status', '').lower()
    
    # Chapa payment statuses: 'success', 'pending', 'failed'
    if payment_status == 'success':
        # Payment successful
        db.update_transaction_status(tx_ref, 'success')
        
        # Generate bingo card
        card = BingoGame.generate_card()
        
        # Add player to game
        game_id = transaction['game_id']
        user_data = db.get_user(user.id)
        
        if db.add_player(game_id, user_data['id'], card):
            # Get player count
            players = db.get_players(game_id)
            
            test_badge = "🧪 [TEST MODE] " if TEST_MODE else ""
            
            await query.edit_message_text(
                f"✅ {test_badge}Payment Verified!\n\n"
                f"You've joined Game #{game_id}\n"
                f"Players: {len(players)}\n\n"
                f"Use /my_card to view your bingo card\n"
                f"Waiting for game to start..."
            )
            
            # Notify chat
            await context.bot.send_message(
                chat_id=db.get_game(game_id)['chat_id'],
                text=f"🎉 {user.first_name} joined the game! ({len(players)} players)"
            )
        else:
            await query.edit_message_text("❌ Failed to join game. You may have already joined.")
    else:
        # Payment not completed yet
        payment_data = verification.get('data', {})
        await query.edit_message_text(
            f"⏳ Payment Status: {payment_status.upper()}\n\n"
            f"Amount: {payment_data.get('amount', 'N/A')} ETB\n"
            f"Please complete the payment and try again.\n\n"
            f"If you've already paid, wait a moment and click verify again."
        )


async def start_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start_game command"""
    chat_id = update.effective_chat.id
    
    # Get active game
    game = db.get_active_game(chat_id)
    if not game:
        await update.message.reply_text("❌ No active game found!")
        return
    
    if game['status'] != 'waiting':
        await update.message.reply_text("❌ Game has already started!")
        return
    
    # Check minimum players (1 in test mode, 2 in production)
    min_players = 1 if TEST_MODE else 2
    players = db.get_players(game['id'])
    if len(players) < min_players:
        await update.message.reply_text(
            f"❌ Need at least {min_players} player(s) to start!\n"
            f"Current players: {len(players)}"
        )
        return
    
    # Start game
    db.update_game_status(game['id'], 'active')
    
    await update.message.reply_text(
        f"🎮 Game Starting in 5 seconds!\n\n"
        f"Players: {len(players)}\n"
        f"Total Pool: {game['total_pool']} ETB\n"
        f"Prize: {game['total_pool'] * (1 - COMMISSION_PERCENT / 100):.2f} ETB"
    )
    
    # Start game loop
    task = asyncio.create_task(game_loop(game['id'], context))
    active_game_tasks[game['id']] = task


async def game_loop(game_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Main game loop - calls numbers every 5 seconds"""
    await asyncio.sleep(5)  # Initial countdown
    
    game = db.get_game(game_id)
    chat_id = game['chat_id']
    
    await context.bot.send_message(chat_id, "🎲 Game Started! Calling numbers...")
    
    bingo_game = BingoGame()
    
    while True:
        game = db.get_game(game_id)
        
        if game['status'] != 'active':
            break
        
        # Call a number
        number = bingo_game.call_number(game['called_numbers'])
        
        if number is None:
            await context.bot.send_message(chat_id, "🎲 All numbers called! No winner.")
            db.update_game_status(game_id, 'finished')
            break
        
        # Add to called numbers
        db.add_called_number(game_id, number)
        
        # Auto-mark on all player cards
        players = db.get_players(game_id)
        winner = None
        
        for player in players:
            marked = BingoGame.mark_number(player['card'], player['marked'], number)
            db.update_player_marked(game_id, player['user_id'], marked)
            
            # Check for win
            if BingoGame.check_win(player['card'], marked):
                winner = player
                break
        
        # Announce number
        await context.bot.send_message(
            chat_id,
            f"🔢 Number Called: {number}\n"
            f"Total Called: {len(game['called_numbers']) + 1}"
        )
        
        # Check for winner
        if winner:
            await handle_winner(game_id, winner, context)
            break
        
        # Wait 5 seconds before next number
        await asyncio.sleep(5)
    
    # Clean up
    if game_id in active_game_tasks:
        del active_game_tasks[game_id]


async def handle_winner(game_id: int, winner: dict, context: ContextTypes.DEFAULT_TYPE):
    """Handle game winner"""
    game = db.get_game(game_id)
    
    # Calculate prize
    prize = game['total_pool'] * (1 - COMMISSION_PERCENT / 100)
    
    # Update winner
    db.set_winner(game_id, winner['user_id'])
    db.update_user_balance(winner['telegram_id'], prize)
    db.increment_games_played(winner['telegram_id'])
    
    # Create payout transaction
    db.create_transaction(
        user_id=winner['user_id'],
        amount=prize,
        tx_ref=f"payout-{game_id}-{winner['user_id']}",
        transaction_type='payout',
        game_id=game_id
    )
    db.update_transaction_status(f"payout-{game_id}-{winner['user_id']}", 'success')
    
    # Announce winner
    card_display = BingoGame.format_card(winner['card'], winner['marked'])
    
    await context.bot.send_message(
        game['chat_id'],
        f"🎉🎉🎉 BINGO! 🎉🎉🎉\n\n"
        f"Winner: @{winner['username'] or winner['telegram_id']}\n"
        f"Prize: {prize:.2f} ETB\n\n"
        f"Winning Card:\n```\n{card_display}\n```",
        parse_mode='Markdown'
    )


async def my_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /my_card command"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Get active game
    game = db.get_active_game(chat_id)
    if not game:
        await update.message.reply_text("❌ No active game in this chat!")
        return
    
    # Get user data
    user_data = db.get_user(user.id)
    if not user_data:
        await update.message.reply_text("❌ You haven't joined any game!")
        return
    
    # Get player
    player = db.get_player(game['id'], user_data['id'])
    if not player:
        await update.message.reply_text("❌ You haven't joined this game!")
        return
    
    # Format card
    card_display = BingoGame.format_card(player['card'], player['marked'])
    
    await update.message.reply_text(
        f"🎴 Your Bingo Card (Game #{game['id']})\n\n"
        f"```\n{card_display}\n```\n\n"
        f"Marked: {len(player['marked'])} numbers",
        parse_mode='Markdown'
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /balance command"""
    user = update.effective_user
    user_data = db.get_user(user.id)
    
    if not user_data:
        await update.message.reply_text("❌ User not found. Use /start first!")
        return
    
    await update.message.reply_text(
        f"💰 Your Balance\n\n"
        f"Balance: {user_data['balance']:.2f} ETB\n"
        f"Games Played: {user_data['games_played']}"
    )


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /leaderboard command"""
    top_players = db.get_leaderboard(10)
    
    if not top_players:
        await update.message.reply_text("📊 No players yet!")
        return
    
    leaderboard_text = "🏆 Top 10 Players\n\n"
    for idx, player in enumerate(top_players, 1):
        username = player['username'] or 'Anonymous'
        leaderboard_text += (
            f"{idx}. @{username}\n"
            f"   💰 {player['balance']:.2f} ETB | 🎮 {player['games_played']} games\n\n"
        )
    
    await update.message.reply_text(leaderboard_text)


def main():
    """Start the bot"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables!")
        return
    
    if not CHAPA_SECRET_KEY:
        logger.error("CHAPA_SECRET_KEY not found in environment variables!")
        return
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create_game", create_game))
    application.add_handler(CommandHandler("join_game", join_game))
    application.add_handler(CommandHandler("start_game", start_game_command))
    application.add_handler(CommandHandler("my_card", my_card))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("leaderboard", leaderboard))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(handle_join_callback, pattern="^join_"))
    application.add_handler(CallbackQueryHandler(handle_verify_callback, pattern="^verify_"))
    
    # Start bot
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

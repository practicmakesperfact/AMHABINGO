import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import sys
import os

# Add the backend directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import get_settings
from bot_api_client import BotAPIClient

settings = get_settings()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Initialize API client (Bot → API → Database)
api_client = BotAPIClient(settings.BACKEND_URL)

CHANNEL = "@amhabingo"
GROUP   = "@amhabingochat"

# ── Keyboards ─────────────────────────────────────────────────────────────────
def get_main_menu_kb():
    """Main menu matching Beteseb Bingo layout (5 rows, 2 per row)."""
    webapp_url = settings.FRONTEND_URL

    # Telegram Web Apps require HTTPS
    if webapp_url.startswith("http://"):
        webapp_url = None
        print("⚠️  WARNING: Telegram Web Apps need HTTPS. FRONTEND_URL must be an ngrok / production URL.")

    play_btn = (
        KeyboardButton(text="Play 🎮", web_app=WebAppInfo(url=webapp_url))
        if webapp_url
        else KeyboardButton(text="Play 🎮")
    )

    kb = [
        [play_btn,                                 KeyboardButton(text="Register 📋", request_contact=True)],
        [KeyboardButton(text="Check Balance 💵"),  KeyboardButton(text="Deposit 💰")],
        [KeyboardButton(text="Contact Support ☎️"),KeyboardButton(text="Instruction 📖")],
        [KeyboardButton(text="Transfer 🎁"),        KeyboardButton(text="Withdraw 🤑")],
        [KeyboardButton(text="Invite 🔗"),          KeyboardButton(text="Convert Bonus 💲")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# ── /start ────────────────────────────────────────────────────────────────────
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🎲 *Welcome to AMHABINGO!* Choose an Option below.\n\n"
        "📋 ለማጫወት ፊርማ ሰጥቶ *Register* ይጫኑ።\n"
        "🎮 ከዛ *Play* ብለው ጨዋታ ይጀምሩ!",
        reply_markup=get_main_menu_kb(),
        parse_mode="Markdown",
    )


# ── /help ─────────────────────────────────────────────────────────────────────
@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🆘 *AMHABINGO Help*\n\n"
        "• *Register* — ስልክ ቁጥርዎን ያጋሩ (10 ETB ቦነስ ያገኛሉ)\n"
        "• *Play* — ጨዋታ ይጀምሩ\n"
        "• *Check Balance* — ቀሪ ሒሳብ ያረጋግጡ\n"
        "• *Deposit* — ገንዘብ ይጨምሩ\n"
        "• *Withdraw* — ገንዘብ ያወጡ\n"
        "• *Transfer* — ወደ ሌሎች ያስተላልፉ\n"
        "• *Invite* — ጓደኛዎን ይጋብዙ\n\n"
        f"📢 Channel: {CHANNEL}\n"
        f"👥 Group: {GROUP}",
        parse_mode="Markdown",
    )


# ── Contact → Register ────────────────────────────────────────────────────────
@dp.message(F.contact)
async def handle_contact(message: types.Message):
    """
    Register user via contact share.
    NOW USES API instead of direct database access! ✅
    """
    contact = message.contact
    if not contact:
        return

    telegram_id  = contact.user_id if contact.user_id else message.from_user.id
    phone_number = contact.phone_number

    try:
        # Call FastAPI endpoint (Bot → API → Database)
        user = await api_client.register_user(
            telegram_id=telegram_id,
            phone_number=phone_number,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )

        # Check if this was a new registration or update
        if user.get('play_balance', 0) == 10.0 and user.get('games_played', 0) == 0:
            # New user
            await message.answer(
                "🎉 ✅ Player registered successfully!\n\n"
                "✨ አዲስ መረጃዎቸን እንዲደርሱት ቻናልችንን እና ግሩፓችንን ይቀላቀሉ።\n\n"
                f"📢 Channel: {CHANNEL}\n"
                f"👥 Group: {GROUP}\n\n"
                "🎁 *10 ETB* ቦነስ Play Wallet ላይ ተጨምሯል!\n"
                "👉 *Play 🎮* ይጫኑ ጨዋታ ለመጀምር!",
                parse_mode="Markdown",
                reply_markup=get_main_menu_kb(),
            )
        else:
            # Existing user
            await message.answer(
                "✅ ቀደም ብለው ተመዝግበዋል!\n\n"
                f"💰 Main Wallet: *{user.get('balance', 0):.2f} ETB*\n"
                f"🎮 Play Wallet: *{user.get('play_balance', 0):.2f} ETB*\n\n"
                "👉 *Play 🎮* ይጫኑ ጨዋታ ለመጀምር!",
                parse_mode="Markdown",
                reply_markup=get_main_menu_kb(),
            )

    except Exception as e:
        logging.error(f"Registration error: {e}")
        await message.answer(
            "❌ Registration failed. Please try again or contact support.",
            reply_markup=get_main_menu_kb(),
        )


# ── Check Balance ─────────────────────────────────────────────────────────────
@dp.message(F.text == "Check Balance 💵")
async def check_balance(message: types.Message):
    """
    Check user balance via API.
    NOW USES API instead of direct database access! ✅
    """
    telegram_id = message.from_user.id
    
    try:
        # Call FastAPI endpoint (Bot → API → Database)
        balance_data = await api_client.get_user_balance(telegram_id)
        
        await message.answer(
            f"💰 *የሒሳብ ቀሪ*\n\n"
            f"🏦 Main Wallet: *{balance_data['balance']:.2f} ETB*\n"
            f"🎮 Play Wallet: *{balance_data['play_balance']:.2f} ETB*\n"
            f"🪙 Coins: *{balance_data['coins']}*\n"
            f"💵 Total: *{balance_data['total']:.2f} ETB*",
            parse_mode="Markdown",
        )
    
    except Exception as e:
        if "404" in str(e):
            await message.answer(
                "❌ ተመዝግበው አልቀረቡም። *Register 📋* ይጫኑ ።",
                parse_mode="Markdown",
            )
        else:
            logging.error(f"Balance check error: {e}")
            await message.answer(
                "❌ Could not fetch balance. Please try again.",
            )


# ── Deposit ───────────────────────────────────────────────────────────────────
@dp.message(F.text == "Deposit 💰")
async def handle_deposit(message: types.Message):
    await message.answer(
        "💰 *Deposit — ገንዘብ ይጨምሩ*\n\n"
        "አሁን ለ Deposit፣ ቦቱን ያናግሩ ወይም ቻናላችንን ይቀላቀሉ:\n\n"
        f"📢 {CHANNEL}\n"
        f"👥 {GROUP}\n\n"
        "⏳ Online payment integration coming soon!",
        parse_mode="Markdown",
    )


# ── Withdraw ──────────────────────────────────────────────────────────────────
@dp.message(F.text == "Withdraw 🤑")
async def handle_withdraw(message: types.Message):
    """
    Withdraw handler - checks balance via API.
    NOW USES API instead of direct database access! ✅
    """
    telegram_id = message.from_user.id
    
    try:
        # Call FastAPI endpoint (Bot → API → Database)
        balance_data = await api_client.get_user_balance(telegram_id)
        
        if balance_data['balance'] < 50:
            await message.answer(
                f"❌ *Withdraw አይቻልም!*\n\n"
                f"ቀሪ ሒሳብ: *{balance_data['balance']:.2f} ETB*\n"
                f"ዝቅተኛ withdraw: *50 ETB*\n\n"
                "🎮 ጨዋታ ይጫወቱ balance ይጨምሩ!",
                parse_mode="Markdown",
            )
            return

        await message.answer(
            f"🤑 *Withdraw — ገንዘብ ያወጡ*\n\n"
            f"💰 ያሎት ሒሳብ: *{balance_data['balance']:.2f} ETB*\n\n"
            "ለ withdraw ቻናልን ይቀላቀሉ:\n"
            f"📢 {CHANNEL}\n"
            f"👥 {GROUP}\n\n"
            "⏳ Automated withdrawal coming soon!",
            parse_mode="Markdown",
        )
    
    except Exception as e:
        if "404" in str(e):
            await message.answer(
                "❌ ተመዝግበው አልቀረቡም። *Register 📋* ይጫኑ።",
                parse_mode="Markdown"
            )
        else:
            logging.error(f"Withdraw check error: {e}")
            await message.answer("❌ Could not process request. Please try again.")


# ── Transfer ──────────────────────────────────────────────────────────────────
@dp.message(F.text == "Transfer 🎁")
async def handle_transfer(message: types.Message):
    await message.answer(
        "🎁 *Transfer — ወደ ሌሎች ያስተላልፉ*\n\n"
        "ገንዘብ ለሌሎች ተጫዋቾች ለማስተላለፍ:\n\n"
        f"📢 ቻናል: {CHANNEL}\n"
        f"👥 ግሩፕ: {GROUP}\n\n"
        "⏳ Transfer feature coming soon!",
        parse_mode="Markdown",
    )


# ── Invite ────────────────────────────────────────────────────────────────────
@dp.message(F.text == "Invite 🔗")
async def handle_invite(message: types.Message):
    bot_info  = await bot.get_me()
    invite_url = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    await message.answer(
        "🔗 *ጓደኛዎን ይጋብዙ!*\n\n"
        "ይህን ሊንክ ጓደኞቸዎ ያጋሩ:\n\n"
        f"`{invite_url}`\n\n"
        "📢 ቻናላችንንም ያጋሩ:\n"
        f"{CHANNEL}",
        parse_mode="Markdown",
    )


# ── Convert Bonus ─────────────────────────────────────────────────────────────
@dp.message(F.text == "Convert Bonus 💲")
async def handle_convert_bonus(message: types.Message):
    """
    Convert bonus handler - checks coins via API.
    NOW USES API instead of direct database access! ✅
    """
    telegram_id = message.from_user.id
    
    try:
        # Call FastAPI endpoint (Bot → API → Database)
        balance_data = await api_client.get_user_balance(telegram_id)
        
        await message.answer(
            f"💲 *Convert Bonus*\n\n"
            f"🪙 ያሎት Coins: *{balance_data['coins']}*\n"
            f"🎮 Play Wallet: *{balance_data['play_balance']:.2f} ETB*\n\n"
            "100 Coins = 1 ETB Play Balance\n\n"
            "⏳ Conversion feature coming soon!",
            parse_mode="Markdown",
        )
    
    except Exception as e:
        if "404" in str(e):
            await message.answer(
                "❌ ተመዝግበው አልቀረቡም። *Register 📋* ይጫኑ።",
                parse_mode="Markdown"
            )
        else:
            logging.error(f"Convert bonus error: {e}")
            await message.answer("❌ Could not process request. Please try again.")


# ── Contact Support ───────────────────────────────────────────────────────────
@dp.message(F.text == "Contact Support ☎️")
async def handle_support(message: types.Message):
    await message.answer(
        "☎️ *Contact Support*\n\n"
        "ለማናቸውም ጥያቄ ወይም ችግር:\n\n"
        f"📢 Channel: {CHANNEL}\n"
        f"👥 Group: {GROUP}\n\n"
        "Support team ይጠብቀዎታል! 🙏",
        parse_mode="Markdown",
    )


# ── Instruction ───────────────────────────────────────────────────────────────
@dp.message(F.text == "Instruction 📖")
async def handle_instruction(message: types.Message):
    await message.answer(
        "📖 *AMHABINGO — አጫወት ስልት*\n\n"
        "1️⃣ *Register* — ስልክ ቁጥርዎን ያጋሩ (10 ETB ቦነስ)\n"
        "2️⃣ *Play* — Stake ይምረጡ (10, 20, 50, 100 ETB)\n"
        "3️⃣ *Cartela* — ካርቴላ ቁጥር ይምረጡ (1-600)\n"
        "4️⃣ *ጨዋታ ይጀምሩ* — ቁጥሮቸ ሲጠሩ ካርቴላዎ ይሞላል\n"
        "5️⃣ *BINGO!* — ረድፍ፣ ዓምድ ወይም ሰያፍ ሞልቶ ያሸንፋሉ\n\n"
        "💰 *Prize = (Players × Stake) × 80%*\n"
        "🏆 ድሉ ወዲያው ወደ Main Wallet ይጨምራል!\n\n"
        f"📢 Channel: {CHANNEL}\n"
        f"👥 Group: {GROUP}",
        parse_mode="Markdown",
    )


# ── Catch-all ─────────────────────────────────────────────────────────────────
@dp.message()
async def catch_all(message: types.Message):
    await message.answer(
        "🤷 ያዘዙትን አላወቅሁም። ከታች ያለውን ሜኑ ይጠቀሙ።",
        reply_markup=get_main_menu_kb(),
    )


# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    print("🤖 Starting AMHABINGO Telegram Bot...")
    print(f"✅ Using API client: {settings.BACKEND_URL}")
    try:
        await dp.start_polling(bot)
    finally:
        # Close API client on shutdown
        await api_client.close()
        print("🛑 Bot stopped, API client closed")


if __name__ == "__main__":
    asyncio.run(main())

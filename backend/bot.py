import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from sqlalchemy import select
import sys
import os

# Add the backend directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models import User

settings = get_settings()

logging.basicConfig(level=logging.INFO)
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

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
    contact = message.contact
    if not contact:
        return

    telegram_id  = contact.user_id if contact.user_id else message.from_user.id
    phone_number = contact.phone_number

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user   = result.scalar_one_or_none()

        if user:
            if not user.phone_number:
                user.phone_number = phone_number
                await db.commit()
                await message.answer(
                    "✅ ስልክ ቁጥርዎ ተዘምኗል! ተመዝግበዋል።\n\n"
                    "👉 *Play 🎮* ይጫኑ ጨዋታ ለመጀምር!",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu_kb(),
                )
            else:
                await message.answer(
                    "✅ ቀደም ብለው ተመዝግበዋል!\n\n"
                    f"💰 Main Wallet: *{user.balance:.2f} ETB*\n"
                    f"🎮 Play Wallet: *{user.play_balance:.2f} ETB*\n\n"
                    "👉 *Play 🎮* ይጫኑ ጨዋታ ለመጀምር!",
                    parse_mode="Markdown",
                    reply_markup=get_main_menu_kb(),
                )
        else:
            # New user — give 10 ETB play bonus
            user = User(
                telegram_id  = telegram_id,
                phone_number = phone_number,
                username     = message.from_user.username,
                first_name   = message.from_user.first_name,
                last_name    = message.from_user.last_name,
                balance      = 0.0,
                play_balance = 10.0,   # FREE BONUS
                coins        = 0,
            )
            db.add(user)
            await db.commit()

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


# ── Check Balance ─────────────────────────────────────────────────────────────
@dp.message(F.text == "Check Balance 💵")
async def check_balance(message: types.Message):
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user   = result.scalar_one_or_none()

    if not user:
        await message.answer(
            "❌ ተመዝግበው አልቀረቡም። *Register 📋* ይጫኑ ።",
            parse_mode="Markdown",
        )
        return

    await message.answer(
        f"💰 *የሒሳብ ቀሪ*\n\n"
        f"🏦 Main Wallet: *{user.balance:.2f} ETB*\n"
        f"🎮 Play Wallet: *{user.play_balance:.2f} ETB*\n"
        f"🪙 Coins: *{user.coins}*\n"
        f"🏆 Wins: *{user.wins}*",
        parse_mode="Markdown",
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
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user   = result.scalar_one_or_none()

    if not user:
        await message.answer("❌ ተመዝግበው አልቀረቡም። *Register 📋* ይጫኑ።", parse_mode="Markdown")
        return

    if user.balance < 50:
        await message.answer(
            f"❌ *Withdraw አይቻልም!*\n\n"
            f"ቀሪ ሒሳብ: *{user.balance:.2f} ETB*\n"
            f"ዝቅተኛ withdraw: *50 ETB*\n\n"
            "🎮 ጨዋታ ይጫወቱ balance ይጨምሩ!",
            parse_mode="Markdown",
        )
        return

    await message.answer(
        f"🤑 *Withdraw — ገንዘብ ያወጡ*\n\n"
        f"💰 ያሎት ሒሳብ: *{user.balance:.2f} ETB*\n\n"
        "ለ withdraw ቻናልን ይቀላቀሉ:\n"
        f"📢 {CHANNEL}\n"
        f"👥 {GROUP}\n\n"
        "⏳ Automated withdrawal coming soon!",
        parse_mode="Markdown",
    )


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
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user   = result.scalar_one_or_none()

    if not user:
        await message.answer("❌ ተመዝግበው አልቀረቡም። *Register 📋* ይጫኑ።", parse_mode="Markdown")
        return

    await message.answer(
        f"💲 *Convert Bonus*\n\n"
        f"🪙 ያሎት Coins: *{user.coins}*\n"
        f"🎮 Play Wallet: *{user.play_balance:.2f} ETB*\n\n"
        "100 Coins = 1 ETB Play Balance\n\n"
        "⏳ Conversion feature coming soon!",
        parse_mode="Markdown",
    )


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
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

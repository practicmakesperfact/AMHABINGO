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

# ── Keyboards ─────────────────────────────────────────────────────────────────
def get_main_menu_kb():
    # Matches the screenshot: Play, Register, Check Balance, Deposit, Contact Support, etc.
    # Telegram requires HTTPS for WebApp URLs
    webapp_url = settings.FRONTEND_URL
    if webapp_url.startswith("http://"):
        webapp_url = "https://example.com"  # Placeholder to prevent crash
        print("⚠️ WARNING: Telegram Web Apps require HTTPS. Please update FRONTEND_URL in .env to an ngrok or production HTTPS URL.")
        
    kb = [
        [
            KeyboardButton(text="Play 🎮", web_app=WebAppInfo(url=webapp_url)),
            KeyboardButton(text="Register 📝", request_contact=True)
        ],
        [
            KeyboardButton(text="Check Balance 💵"),
            KeyboardButton(text="Deposit 💰")
        ],
        [
            KeyboardButton(text="Contact Support ☎️"),
            KeyboardButton(text="Instruction 📖")
        ],
        [
            KeyboardButton(text="Transfer 🎁"),
            KeyboardButton(text="Withdraw 🤑")
        ],
        [
            KeyboardButton(text="Invite 🔗"),
            KeyboardButton(text="Convert Bonus 💲")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# ── Handlers ──────────────────────────────────────────────────────────────────
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Welcome to AMHABINGO! Choose an Option below.",
        reply_markup=get_main_menu_kb()
    )

@dp.message(F.contact)
async def handle_contact(message: types.Message):
    contact = message.contact
    if not contact:
        return
        
    telegram_id = contact.user_id if contact.user_id else message.from_user.id
    phone_number = contact.phone_number
    
    async with AsyncSessionLocal() as db:
        # Check if user exists
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        
        if user:
            if not user.phone_number:
                user.phone_number = phone_number
                await db.commit()
                await message.answer("✅ Contact info updated! You are already registered.")
            else:
                await message.answer("✅ You are already registered and your contact is saved.")
        else:
            # New user registration - Give 10 ETB Play Balance Bonus
            user = User(
                telegram_id=telegram_id,
                phone_number=phone_number,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                balance=0.0,
                play_balance=10.0, # FREE BONUS
                coins=0
            )
            db.add(user)
            await db.commit()
            
            await message.answer(
                "🎉 Registration Successful!\n\n"
                "You have been credited with a **10 ETB free bonus** in your Play Wallet!\n"
                "Click **Play 🎮** to start playing.",
                parse_mode="Markdown"
            )

@dp.message(F.text == "Check Balance 💵")
async def check_balance(message: types.Message):
    telegram_id = message.from_user.id
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer("You are not registered yet. Please click 'Register 📝' first.")
            return
            
        await message.answer(
            f"💰 **Your Wallet Balance**\n\n"
            f"**Main Wallet:** {user.balance:.2f} ETB\n"
            f"**Play Wallet:** {user.play_balance:.2f} ETB\n"
            f"**Coins:** {user.coins}",
            parse_mode="Markdown"
        )

# Fallback for other buttons
@dp.message(F.text.in_(["Deposit 💰", "Contact Support ☎️", "Instruction 📖", "Transfer 🎁", "Withdraw 🤑", "Invite 🔗", "Convert Bonus 💲"]))
async def fallback_buttons(message: types.Message):
    await message.answer("This feature is coming soon!")

# Catch-all for unknown commands or text
@dp.message()
async def catch_all(message: types.Message):
    await message.answer(
        "I don't recognize that command! Please use the menu buttons below to navigate, or click **Play 🎮** to open the game app.",
        reply_markup=get_main_menu_kb(),
        parse_mode="Markdown"
    )

# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    print("🤖 Starting Telegram Bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

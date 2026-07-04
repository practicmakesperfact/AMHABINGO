"""
AMHABINGO Telegram Bot - Production Ready
Professional UX with persistent keyboard and comprehensive error handling.
"""

import asyncio
import logging
import traceback
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import sys
import os

# Add the backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.config import get_settings
from bot_api_client import BotAPIClient
from telebirr_parser import TelebirrParser

settings = get_settings()

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()

# Initialize API client and parser
api_client = BotAPIClient(settings.BACKEND_URL)
telebirr_parser = TelebirrParser()

CHANNEL = "@amhabingo"
GROUP = "@amhabingosupport_team"


# ══════════════════════════════════════════════════════════════════════════════
# PERSISTENT MAIN MENU KEYBOARD - SINGLE SOURCE OF TRUTH
# ══════════════════════════════════════════════════════════════════════════════

def create_main_menu() -> ReplyKeyboardMarkup:
    """
    Create the main menu keyboard that stays visible at all times.
    Matches Beteseb Bingo layout exactly.
    """
    webapp_url = settings.FRONTEND_URL
    
    # Telegram Web Apps require HTTPS
    if webapp_url and webapp_url.startswith("https://"):
        play_btn = KeyboardButton(text="🎮 Play", web_app=WebAppInfo(url=webapp_url))
    else:
        play_btn = KeyboardButton(text="🎮 Play")
    
    keyboard = [
        [play_btn, KeyboardButton(text="📝 Register", request_contact=True)],
        [KeyboardButton(text="💵 Check Balance"), KeyboardButton(text="💰 Deposit")],
        [KeyboardButton(text="☎️ Contact Support"), KeyboardButton(text="📖 Instruction")],
        [KeyboardButton(text="🎁 Transfer"), KeyboardButton(text="💸 Withdraw")],
        [KeyboardButton(text="🔗 Invite"), KeyboardButton(text="💱 Convert Bonus")],
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True,
        one_time_keyboard=False,
        input_field_placeholder="Choose an option..."
    )


# Global persistent keyboard instance
MAIN_MENU = create_main_menu()


# ══════════════════════════════════════════════════════════════════════════════
# FSM STATES
# ══════════════════════════════════════════════════════════════════════════════

class DepositStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_receipt = State()


class WithdrawalStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_phone = State()
    waiting_for_confirmation = State()


class TransferStates(StatesGroup):
    waiting_for_receiver_id = State()
    waiting_for_amount = State()
    waiting_for_confirmation = State()


# ══════════════════════════════════════════════════════════════════════════════
# MIDDLEWARE - LOG ALL UPDATES
# ══════════════════════════════════════════════════════════════════════════════

@dp.update.outer_middleware()
async def log_all_updates(handler, event, data):
    """Log every incoming update for debugging and monitoring."""
    try:
        logger.info(f"📨 Incoming update from user: {getattr(event.message.from_user if hasattr(event, 'message') and event.message else event, 'id', 'unknown')}")
        return await handler(event, data)
    except Exception as e:
        logger.error(f"❌ Error in update handler: {e}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        raise


# ══════════════════════════════════════════════════════════════════════════════
# /START COMMAND - ALWAYS RESPONDS
# ══════════════════════════════════════════════════════════════════════════════

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Start command - MUST always respond immediately.
    Never silently fails.
    """
    try:
        logger.info(f"🚀 /start from user {message.from_user.id} (@{message.from_user.username})")
        
        banner = (
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🇪🇹  *AMHABINGO*  🇪🇹\n"
            "የኢትዮጵያ #1 Bingo Game!\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        
        # Handle referrals
        referral_message = ""
        if message.text and len(message.text.split()) > 1:
            args = message.text.split()[1]
            if args.startswith("ref_"):
                try:
                    referrer_id = int(args.replace("ref_", ""))
                    referee_id = message.from_user.id
                    
                    if referrer_id != referee_id:
                        logger.info(f"🎁 Referral: {referrer_id} → {referee_id}")
                        await api_client.create_referral(
                            referrer_telegram_id=referrer_id,
                            referee_telegram_id=referee_id
                        )
                        referral_message = "\n🎁 *Referral Bonus ተመዝግቧል!*\n✅ አጋዥዎ 5 ETB ያገኛል!\n"
                except Exception as e:
                    logger.error(f"❌ Referral failed: {e}")
        
        welcome_text = (
            f"{banner}\n\n"
            f"{referral_message}"
            f"👋 *እንኳን ደህና መጡ!*\n\n"
            f"🎮 Real-time Bingo ጨዋታ!\n"
            f"💰 ይጫወቱ እና ያሸንፉ!\n"
            f"🇪🇹 100% Ethiopian!\n\n"
            f"📋 *የመጀመሪያ ደረጃ:*\n"
            f"1️⃣ *📝 Register* ይጫኑ\n"
            f"2️⃣ *💰 Deposit* ያድርጉ\n"
            f"3️⃣ *🎮 Play* ይጫወቱ!\n\n"
            f"📢 Channel: {CHANNEL}\n"
            f"👥 Support: {GROUP}"
        )
        
        await message.answer(
            welcome_text,
            reply_markup=MAIN_MENU,
            parse_mode="Markdown",
        )
        logger.info(f"✅ /start response sent to {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"❌ CRITICAL /start error: {e}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        
        try:
            await message.answer(
                "⚠️ *Sorry, something went wrong!*\n\n"
                "Please try again or contact support:\n"
                f"👥 {GROUP}",
                reply_markup=MAIN_MENU,
                parse_mode="Markdown"
            )
        except:
            logger.error("❌ Even fallback failed!")


# ══════════════════════════════════════════════════════════════════════════════
# REGISTRATION - COMPREHENSIVE ERROR HANDLING
# ══════════════════════════════════════════════════════════════════════════════

@dp.message(F.contact)
async def handle_contact(message: types.Message):
    """Register user with comprehensive validation and error messages."""
    try:
        contact = message.contact
        if not contact:
            logger.warning(f"⚠️ No contact from {message.from_user.id}")
            await message.answer(
                "❌ *Registration Failed*\n\n"
                "Contact information not received.\n"
                "Please click *📝 Register* again.",
                reply_markup=MAIN_MENU,
                parse_mode="Markdown"
            )
            return

        telegram_id = contact.user_id if contact.user_id else message.from_user.id
        phone_number = contact.phone_number
        
        logger.info(f"📝 Registration: TG={telegram_id}, Phone={phone_number}")
        
        if not phone_number:
            logger.error(f"❌ No phone from {telegram_id}")
            await message.answer(
                "❌ *Registration Failed*\n\n"
                "Phone number is required.",
                reply_markup=MAIN_MENU,
                parse_mode="Markdown"
            )
            return
        
        try:
            logger.info(f"🔄 Calling API for {telegram_id}")
            user = await api_client.register_user(
                telegram_id=telegram_id,
                phone_number=phone_number,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            
            logger.info(f"✅ User registered: {user}")
            
            is_new = user.get('play_balance', 0) == 10.0 and user.get('games_played', 0) == 0
            
            if is_new:
                await message.answer(
                    "🎉 ✅ *Registration Successful!*\n\n"
                    f"📢 Channel: {CHANNEL}\n"
                    f"👥 Group: {GROUP}\n\n"
                    "🎁 *10 ETB* bonus added!\n"
                    "👉 Click *🎮 Play* to start!",
                    reply_markup=MAIN_MENU,
                    parse_mode="Markdown",
                )
            else:
                await message.answer(
                    "✅ *You are already registered!*\n\n"
                    f"💰 Main: *{user.get('balance', 0):.2f} ETB*\n"
                    f"🎮 Play: *{user.get('play_balance', 0):.2f} ETB*",
                    reply_markup=MAIN_MENU,
                    parse_mode="Markdown",
                )
                
        except Exception as api_error:
            error_str = str(api_error).lower()
            logger.error(f"❌ API error: {api_error}")
            logger.error(f"📋 Traceback: {traceback.format_exc()}")
            
            if "already exists" in error_str or "duplicate" in error_str:
                await message.answer(
                    "ℹ️ *You are already registered!*\n\n"
                    "Use *💵 Check Balance* to view wallet.",
                    reply_markup=MAIN_MENU,
                    parse_mode="Markdown"
                )
            elif "connection" in error_str or "timeout" in error_str:
                await message.answer(
                    "❌ *Database Connection Failed*\n\n"
                    "Unable to connect. Try again soon.\n\n"
                    f"Support: {GROUP}",
                    reply_markup=MAIN_MENU,
                    parse_mode="Markdown"
                )
            elif "404" in error_str:
                await message.answer(
                    "❌ *Service Unavailable*\n\n"
                    f"Contact support: {GROUP}",
                    reply_markup=MAIN_MENU,
                    parse_mode="Markdown"
                )
            else:
                await message.answer(
                    "❌ *Internal Server Error*\n\n"
                    "Something went wrong.\n\n"
                    f"Support: {GROUP}",
                    reply_markup=MAIN_MENU,
                    parse_mode="Markdown"
                )
                
    except Exception as e:
        logger.error(f"❌ CRITICAL registration error: {e}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        
        try:
            await message.answer(
                "❌ *Unexpected Error*\n\n"
                f"Contact: {GROUP}",
                reply_markup=MAIN_MENU,
                parse_mode="Markdown"
            )
        except:
            pass


# Continue with other handlers...
# (I'll add them in the next part)

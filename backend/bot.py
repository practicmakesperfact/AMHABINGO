import asyncio
import logging
import traceback
import httpx
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
import sys
import os

# Add the backend directory to path so we can import modules
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

# Initialize API client (Bot → API → Database)
api_client = BotAPIClient(settings.BACKEND_URL)

# Initialize Telebirr parser
telebirr_parser = TelebirrParser()

CHANNEL = "@amhabingo"
GROUP   = "@amhabingosupport_team"


# ══════════════════════════════════════════════════════════════════════════════
# PERSISTENT MAIN MENU KEYBOARD - SINGLE SOURCE OF TRUTH
# ══════════════════════════════════════════════════════════════════════════════

def create_main_menu() -> ReplyKeyboardMarkup:
    """
    Create the main menu keyboard that stays visible at all times.
    This is the ONLY keyboard used throughout the bot for consistency.
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
    """FSM states for deposit flow."""
    waiting_for_amount = State()
    waiting_for_receipt = State()


class WithdrawalStates(StatesGroup):
    """FSM states for withdrawal flow."""
    waiting_for_amount = State()
    waiting_for_phone = State()
    waiting_for_confirmation = State()


class TransferStates(StatesGroup):
    """FSM states for transfer flow."""
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
        logger.info(f"📨 Incoming update: {event}")
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
    Start command - MUST always respond.
    Handles referrals if user comes from referral link.
    Format: /start ref_123456789
    """
    try:
        logger.info(f"🚀 /start command from user {message.from_user.id}")
        
        # AMHABINGO Banner
        banner = (
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "🇪🇹  *AMHABINGO*  🇪🇹\n"
            "የኢትዮጵያ #1 Bingo Game!\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        
        # Check if this is a referral
        referral_message = ""
        if message.text and len(message.text.split()) > 1:
            args = message.text.split()[1]
            if args.startswith("ref_"):
                try:
                    referrer_id = int(args.replace("ref_", ""))
                    referee_id = message.from_user.id
                    
                    # Don't process if user refers themselves
                    if referrer_id != referee_id:
                        logger.info(f"🎁 Processing referral: {referrer_id} → {referee_id}")
                        await api_client.create_referral(
                            referrer_telegram_id=referrer_id,
                            referee_telegram_id=referee_id
                        )
                        referral_message = "\n🎁 *የ Referral Bonus ተመዝግቧል!*\n✅ አጋዥዎ 5 ETB ያገኛል!\n"
                        logger.info(f"✅ Referral created successfully")
                except ValueError as e:
                    logger.error(f"❌ Invalid referrer ID: {e}")
                except Exception as e:
                    logger.error(f"❌ Referral creation failed: {e}")
                    logger.error(f"📋 Traceback: {traceback.format_exc()}")
        
        # Welcome message
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
        logger.info(f"✅ /start response sent successfully")
        
    except Exception as e:
        logger.error(f"❌ CRITICAL ERROR in /start handler: {e}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        
        # Always send a response, even if initialization fails
        try:
            await message.answer(
                "⚠️ *Sorry, something went wrong!*\n\n"
                "Please try again or contact support:\n"
                f"👥 {GROUP}",
                reply_markup=MAIN_MENU,
                parse_mode="Markdown"
            )
        except Exception as fallback_error:
            logger.error(f"❌ Even fallback response failed: {fallback_error}")


# ── Commands ─────────────────────────────────────────────────────────────────

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🆘 *AMHABINGO Help*\n\n"
        "• *Register 📋* — ስልክ ቁጥርዎን ያጋሩ (10 ETB ቦነስ)\n"
        "• *Play 🎮* — ጨዋታ ይጀምሩ\n"
        "• *Check Balance 💵* — ቀሪ ሒሳብ ያረጋግጡ\n"
        "• *Deposit 💰* — ገንዘብ ይጨምሩ\n"
        "• *Withdraw 🤑* — ገንዘብ ያወጡ\n"
        "• *Transfer 🎁* — ወደ ሌሎች ያስተላልፉ\n"
        "• *Invite 🔗* — ጓደኞችን ይጋብዙ\n"
        "• *Convert Bonus 💲* — Coins ቀይሩ\n\n"
        f"📢 Channel: {CHANNEL}\n"
        f"👥 Support: {GROUP}",
        parse_mode="Markdown",
    )


# ── Contact → Register ────────────────────────────────────────────────────────
@dp.message(F.contact)
async def handle_contact(message: types.Message):
    """
    Register user via contact share.
    NOW USES API instead of direct database access! ✅
    COMPREHENSIVE ERROR HANDLING - Never fails silently!
    """
    try:
        contact = message.contact
        if not contact:
            logger.warning("❌ No contact in message")
            await message.answer(
                "❌ *Registration Error*\n\n"
                "የእውቂያ መረጃ አልተገኘም።\n"
                "እባክዎን የ *📝 Register* ቁልፉን ይጫኑ።",
                parse_mode="Markdown",
                reply_markup=MAIN_MENU,
            )
            return

        telegram_id  = contact.user_id if contact.user_id else message.from_user.id
        phone_number = contact.phone_number

        if not phone_number:
            logger.error("❌ No phone number in contact")
            await message.answer(
                "❌ *Registration Error*\n\n"
                "የስልክ ቁጥር አልተገኘም።\n"
                "እባክዎን የ *📝 Register* ቁልፉን እንደገና ይጫኑ።",
                parse_mode="Markdown",
                reply_markup=MAIN_MENU,
            )
            return

        logger.info(f"📝 Registering user: telegram_id={telegram_id}, phone={phone_number}")

        # Call FastAPI endpoint (Bot → API → Database)
        user = await api_client.register_user(
            telegram_id=telegram_id,
            phone_number=phone_number,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )

        logger.info(f"✅ Registration successful for user {telegram_id}")

        # Check if this was a new registration or update
        if user.get('play_balance', 0) == 10.0 and user.get('games_played', 0) == 0:
            # New user
            await message.answer(
                "🎉 ✅ *እንኳን ደስ አሎት!*\n\n"
                "በተሳካ ሁኔታ ተመዝግበዋል!\n\n"
                "✨ አዲስ መረጃዎች እንዲደርሱዎት ቻናልችንን እና ግሩፓችንን ይቀላቀሉ።\n\n"
                f"📢 Channel: {CHANNEL}\n"
                f"👥 Group: {GROUP}\n\n"
                "🎁 *10 ETB* ቦነስ Play Wallet ላይ ተጨምሯል!\n"
                "👉 *🎮 Play* ይጫኑ ጨዋታ ለመጀምር!",
                parse_mode="Markdown",
                reply_markup=MAIN_MENU,
            )
        else:
            # Existing user
            await message.answer(
                "✅ *ቀደም ብለው ተመዝግበዋል!*\n\n"
                f"💰 Main Wallet: *{user.get('balance', 0):.2f} ETB*\n"
                f"🎮 Play Wallet: *{user.get('play_balance', 0):.2f} ETB*\n\n"
                "👉 *🎮 Play* ይጫኑ ጨዋታ ለመጀምር!",
                parse_mode="Markdown",
                reply_markup=MAIN_MENU,
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"❌ HTTP error during registration: {e.response.status_code}")
        logger.error(f"📋 Response body: {e.response.text}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        
        if e.response.status_code == 400:
            await message.answer(
                "❌ *Registration Error*\n\n"
                "የተሰጠው መረጃ ትክክል አይደለም።\n"
                "እባክዎን እንደገና ይሞክሩ።",
                parse_mode="Markdown",
                reply_markup=MAIN_MENU,
            )
        elif e.response.status_code == 409:
            await message.answer(
                "✅ *ቀደም ብለው ተመዝግበዋል!*\n\n"
                "የእርስዎ መረጃ በስርዓታችን ውስጥ አለ።\n"
                "👉 *💵 Check Balance* ይጫኑ።",
                parse_mode="Markdown",
                reply_markup=MAIN_MENU,
            )
        elif e.response.status_code == 503:
            await message.answer(
                "❌ *Service Unavailable*\n\n"
                "Database connection failed.\n"
                f"እባክዎን support ያናግሩ: {GROUP}",
                parse_mode="Markdown",
                reply_markup=MAIN_MENU,
            )
        else:
            await message.answer(
                "❌ *Registration Error*\n\n"
                f"Server error ({e.response.status_code}).\n"
                f"እባክዎን support ያናግሩ: {GROUP}",
                parse_mode="Markdown",
                reply_markup=MAIN_MENU,
            )
    
    except httpx.RequestError as e:
        logger.error(f"❌ Network error during registration: {e}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        await message.answer(
            "❌ *Connection Error*\n\n"
            "Could not connect to server.\n"
            "እባክዎን እንደገና ይሞክሩ።\n\n"
            f"Support: {GROUP}",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU,
        )
    
    except Exception as e:
        logger.error(f"❌ Unexpected registration error: {e}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        await message.answer(
            "❌ *Internal Error*\n\n"
            "Unexpected error occurred.\n"
            "እባክዎን support ያናግሩ።\n\n"
            f"Support: {GROUP}",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU,
        )


# ── Check Balance ─────────────────────────────────────────────────────────────
@dp.message(F.text == "💵 Check Balance")
async def check_balance(message: types.Message):
    """
    Check user balance via API - Professional Account Info format.
    NOW USES API instead of direct database access! ✅
    """
    telegram_id = message.from_user.id
    
    try:
        logger.info(f"💵 Balance check requested by user {telegram_id}")
        
        # Call FastAPI endpoint (Bot → API → Database)
        balance_data = await api_client.get_user_balance(telegram_id)
        
        # Get user info from API response
        username = balance_data.get('first_name') or balance_data.get('username') or message.from_user.first_name or "Player"
        phone = balance_data.get('phone_number', 'N/A')
        
        # Format phone number (remove +251 prefix if present)
        if phone and phone.startswith('+251'):
            phone = '0' + phone[4:]
        
        # Professional Account Info format with copyable code block
        account_info = (
            f"� *Account Info*\n\n"
            f"```\n"
            f"Name:          {username}\n"
            f"Phone:         {phone}\n"
            f"Main wallet:   {balance_data['balance']:.1f}\n"
            f"Play wallet:   {balance_data['play_balance']:.1f}\n"
            f"Coin:          {balance_data['coins']}\n"
            f"```"
        )
        
        await message.answer(
            account_info,
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
        
        logger.info(f"✅ Balance sent successfully to user {telegram_id}")
    
    except httpx.HTTPStatusError as e:
        logger.error(f"❌ HTTP error during balance check: {e.response.status_code}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        
        if e.response.status_code == 404:
            await message.answer(
                "❌ *ተመዝግበው አልቀረቡም።*\n\n"
                "እባክዎን *📝 Register* ቁልፉን ይጫኑ።",
                parse_mode="Markdown",
                reply_markup=MAIN_MENU
            )
        else:
            await message.answer(
                "❌ *Service Error*\n\n"
                f"Could not fetch balance (Error {e.response.status_code}).\n"
                f"እባክዎን support ያናግሩ: {GROUP}",
                parse_mode="Markdown",
                reply_markup=MAIN_MENU
            )
    
    except httpx.RequestError as e:
        logger.error(f"❌ Network error during balance check: {e}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        await message.answer(
            "❌ *Connection Error*\n\n"
            "Could not connect to server.\n"
            "እባክዎን እንደገና ይሞክሩ።",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
    
    except Exception as e:
        logger.error(f"❌ Unexpected balance check error: {e}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        await message.answer(
            "❌ *Error*\n\n"
            "Could not fetch balance. Please try again.\n"
            f"Support: {GROUP}",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )


# ── Deposit ───────────────────────────────────────────────────────────────────
@dp.message(F.text == "💰 Deposit")
async def handle_deposit(message: types.Message, state: FSMContext):
    """Start deposit flow - ask for amount."""
    await message.answer(
        "💰 *Deposit — ገንዘብ ይጨምሩ*\n\n"
        "ምን ያህል ገንዘብ deposit ማድረግ ይፈልጋሉ?\n"
        "ዝቅተኛ deposit: *10 ETB*\n\n"
        "የገንዘብ መጠኑን ይላኩ (ምሳሌ: 100)",
        parse_mode="Markdown",
    )
    await state.set_state(DepositStates.waiting_for_amount)


@dp.message(DepositStates.waiting_for_amount)
async def deposit_amount_received(message: types.Message, state: FSMContext):
    """User entered deposit amount."""
    try:
        amount = float(message.text)
        
        if amount < 10:
            await message.answer(
                "❌ ዝቅተኛ deposit መጠን 10 ETB ነው።\n"
                "እባክዎን ከ10 ETB በላይ ያስገቡ።"
            )
            return
        
        # Create deposit via API
        telegram_id = message.from_user.id
        deposit = await api_client.create_deposit(
            telegram_id=telegram_id,
            amount=amount
        )
        
        # Get payment account
        payment_accounts = await api_client.get_payment_accounts()
        if not payment_accounts:
            await message.answer(
                "❌ የክፍያ መረጃ አልተገኘም። እባክዎን support ያናግሩ።"
            )
            await state.clear()
            return
        
        account = payment_accounts[0]  # Get first active account
        
        # Store deposit info in state
        await state.update_data(
            deposit_id=deposit['deposit_id'],
            tx_ref=deposit['tx_ref'],
            amount=amount,
            account_phone=account['phone_number'],
            account_holder=account['account_holder']
        )
        
        # Send payment instructions (your format)
        await message.answer(
            f"💰 *ገንዘብ ማስገባት (Deposit)*\n\n"
            f"የሚያጋጥማቹ የክፍያ ችግር: @amhabingosupport_team ላይ ፃፉልን።\n\n"
            f"*የክፍያ መመሪያዎች:*\n\n"
            f"1️⃣ ከታች ባለው የቴሌብር አካውንት *{amount} ብር* ያስገቡ\n"
            f"   📱 Phone: *{account['phone_number'].replace('+251', '0')}*\n\n"
            f"2️⃣ የከፈሉበትን አጭር የጹሁፍ መልዕክት (message) copy በማድረግ\n"
            f"   እዚህ ላይ Past አድረገው ያስገቡና ይላኩት 👇👇👇\n\n"
            f"📝 Reference: `{deposit['tx_ref']}`",
            parse_mode="Markdown"
        )
        
        await state.set_state(DepositStates.waiting_for_receipt)
        
    except ValueError:
        await message.answer(
            "❌ እባክዎን ትክክለኛ ቁጥር ያስገቡ።\n"
            "ምሳሌ: 100"
        )
    except Exception as e:
        logging.error(f"Deposit creation error: {e}")
        await message.answer(
            "❌ ችግር ተፈጥሯል። እባክዎን እንደገና ይሞክሩ።"
        )
        await state.clear()


@dp.message(DepositStates.waiting_for_receipt)
async def deposit_receipt_received(message: types.Message, state: FSMContext):
    """User sent Telebirr confirmation message."""
    # Get state data
    data = await state.get_data()
    tx_ref = data.get('tx_ref')
    expected_amount = data.get('amount')
    
    if not message.text:
        await message.answer(
            "❌ እባክዎን Telebirr confirmation message forward ያድርጉ።\n"
            "ወይም የላኩትን መጠን እና transaction ID በጽሁፍ ያስገቡ።"
        )
        return
    
    try:
        # Parse Telebirr message
        receipt_data = telebirr_parser.parse(message.text)
        
        if not receipt_data:
            await message.answer(
                "❌ Telebirr message ማንበብ አልተቻለም።\n\n"
                "እባክዎን የሚከተሉትን ያረጋግጡ:\n"
                "• Telebirr confirmation message forward አድርገዋል\n"
                "• Message ሙሉ በሙሉ ተመርጧል\n\n"
                "ወይም በዚህ ቅርጸት ያስገቡ:\n"
                f"Amount: {expected_amount}\n"
                f"Reference: {tx_ref}"
            )
            return
        
        # Validate amount
        if not telebirr_parser.validate_receipt(receipt_data, expected_amount):
            await message.answer(
                f"❌ የገንዘብ መጠን አይመሳሰልም!\n\n"
                f"የጠበቁት: *{expected_amount} ETB*\n"
                f"ከ Telebirr: *{receipt_data.get('amount')} ETB*\n\n"
                "እባክዎን ትክክለኛውን መጠን ያረጋግጡ።",
                parse_mode="Markdown"
            )
            return
        
        # Verify deposit via API
        result = await api_client.verify_deposit(
            tx_ref=tx_ref,
            receipt_data=receipt_data
        )
        
        await message.answer(
            "✅ *Receipt በተሳካ ሁኔታ ገብቷል!*\n\n"
            f"💰 መጠን: *{expected_amount} ETB*\n"
            f"📝 Reference: `{tx_ref}`\n\n"
            "👨‍💼 Admin በ24 ሰዓት ውስጥ ይፈትሻል እና ያፀድቃል።\n"
            "✅ ሲፈቀድ notification ይደርስዎታል።\n\n"
            f"📢 ለበለጠ መረጃ: {CHANNEL}",
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"Receipt verification error: {e}")
        await message.answer(
            "❌ Receipt ማረጋገጥ አልተቻለም።\n"
            "እባክዎን እንደገና ይሞክሩ ወይም support ያናግሩ።"
        )
        await state.clear()


# ── Withdraw ──────────────────────────────────────────────────────────────────
@dp.message(F.text == "💸 Withdraw")
async def handle_withdraw(message: types.Message, state: FSMContext):
    """
    Start withdrawal flow - check balance and ask for amount.
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
            f"💰 ያሎት ሒሳብ: *{balance_data['balance']:.2f} ETB*\n"
            f"ዝቅተኛ withdraw: *50 ETB*\n\n"
            "ምን ያህል ማውጣት ይፈልጋሉ?\n"
            "የገንዘብ መጠኑን ይላኩ (ምሳሌ: 100)",
            parse_mode="Markdown",
        )
        
        # Store balance in state
        await state.update_data(current_balance=balance_data['balance'])
        await state.set_state(WithdrawalStates.waiting_for_amount)
    
    except Exception as e:
        if "404" in str(e):
            await message.answer(
                "❌ ተመዝግበው አልቀረቡም። *Register 📋* ይጫኑ።",
                parse_mode="Markdown"
            )
        else:
            logging.error(f"Withdraw check error: {e}")
            await message.answer("❌ Could not process request. Please try again.")


@dp.message(WithdrawalStates.waiting_for_amount)
async def withdrawal_amount_received(message: types.Message, state: FSMContext):
    """User entered withdrawal amount."""
    try:
        amount = float(message.text)
        data = await state.get_data()
        current_balance = data.get('current_balance', 0)
        
        if amount < 50:
            await message.answer(
                "❌ ዝቅተኛ withdrawal መጠን 50 ETB ነው።"
            )
            return
        
        if amount > current_balance:
            await message.answer(
                f"❌ በቂ ሒሳብ የለዎትም!\n\n"
                f"የጠየቁት: *{amount} ETB*\n"
                f"ያሎት: *{current_balance} ETB*",
                parse_mode="Markdown"
            )
            return
        
        # Store amount and ask for phone
        await state.update_data(amount=amount)
        await message.answer(
            f"💰 Withdrawal መጠን: *{amount} ETB*\n\n"
            f"📱 የ Telebirr ስልክ ቁጥርዎን ያስገቡ\n"
            f"ምሳሌ: +251911223344 ወይም 0911223344",
            parse_mode="Markdown"
        )
        await state.set_state(WithdrawalStates.waiting_for_phone)
        
    except ValueError:
        await message.answer(
            "❌ እባክዎን ትክክለኛ ቁጥር ያስገቡ።\n"
            "ምሳሌ: 100"
        )


@dp.message(WithdrawalStates.waiting_for_phone)
async def withdrawal_phone_received(message: types.Message, state: FSMContext):
    """User entered phone number."""
    phone = message.text.strip()
    
    # Validate phone format
    if not phone or len(phone) < 10:
        await message.answer(
            "❌ ትክክለኛ ስልክ ቁጥር ያስገቡ።\n"
            "ምሳሌ: +251911223344 ወይም 0911223344"
        )
        return
    
    # Format phone number
    formatted_phone = telebirr_parser.format_phone(phone)
    
    # Store phone and show confirmation
    data = await state.get_data()
    amount = data.get('amount')
    
    await state.update_data(phone=formatted_phone)
    
    await message.answer(
        f"📋 *የ Withdrawal መረጃ:*\n\n"
        f"💰 መጠን: *{amount} ETB*\n"
        f"📱 ስልክ: *{formatted_phone}*\n\n"
        f"⚠️ *አስፈላጊ:*\n"
        f"• ገንዘቡ ወዲያውኑ ከሒሳብዎ ይቀነሳል\n"
        f"• Admin ያፀድቃል እና ይልካል\n"
        f"• ከተቀበለ በኋላ ብቻ ያጠናቅቃል\n\n"
        f"ለመቀጠል *አዎ* ይላኩ\n"
        f"ለመሰረዝ *ዋጋ* ይላኩ",
        parse_mode="Markdown"
    )
    await state.set_state(WithdrawalStates.waiting_for_confirmation)


@dp.message(WithdrawalStates.waiting_for_confirmation)
async def withdrawal_confirmation_received(message: types.Message, state: FSMContext):
    """User confirmed or cancelled withdrawal."""
    text = message.text.strip().lower()
    
    if text == "ዋጋ" or text == "cancel":
        await message.answer(
            "❌ Withdrawal ተሰርዟል።",
            reply_markup=MAIN_MENU
        )
        await state.clear()
        return
    
    if text != "አዎ" and text != "yes":
        await message.answer(
            "እባክዎን *አዎ* ለማረጋገጥ ወይም *ዋጋ* ለመሰረዝ ይላኩ።",
            parse_mode="Markdown"
        )
        return
    
    # User confirmed - create withdrawal
    data = await state.get_data()
    amount = data.get('amount')
    phone = data.get('phone')
    telegram_id = message.from_user.id
    
    try:
        # Request withdrawal via API
        result = await api_client.request_withdrawal(
            telegram_id=telegram_id,
            amount=amount,
            phone_number=phone
        )
        
        await message.answer(
            "✅ *Withdrawal ተመዝግቧል!*\n\n"
            f"💰 መጠን: *{amount} ETB*\n"
            f"📱 ስልክ: *{phone}*\n"
            f"📝 Reference: `{result['tx_ref']}`\n\n"
            f"⚠️ ገንዘቡ ከሒሳብዎ ተቀንሷል (held)\n\n"
            f"👨‍💼 Admin በ24 ሰዓት ውስጥ ይፈትሻል\n"
            f"✅ ከተፈቀደ በኋላ ወደ Telebirr ይላካል\n"
            f"📬 Notification ይደርስዎታል\n\n"
            f"📢 Status: {CHANNEL}",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"Withdrawal request error: {e}")
        error_msg = str(e)
        
        if "Insufficient balance" in error_msg:
            await message.answer(
                "❌ በቂ ሒሳብ የለዎትም።",
                reply_markup=MAIN_MENU
            )
        else:
            await message.answer(
                "❌ Withdrawal መጠየቅ አልተቻለም።\n"
                "እባክዎን እንደገና ይሞክሩ።",
                reply_markup=MAIN_MENU
            )
        
        await state.clear()


# ── Transfer ──────────────────────────────────────────────────────────────────
@dp.message(F.text == "🎁 Transfer")
async def handle_transfer(message: types.Message, state: FSMContext):
    """Start transfer flow - ask for receiver telegram ID."""
    await message.answer(
        "🎁 *Transfer — ወደ ሌሎች ያስተላልፉ*\n\n"
        "ገንዘብ ለሌሎች ተጫዋቾች ያስተላልፉ!\n\n"
        "የተቀባዩን Telegram ID ያስገቡ:\n"
        "ምሳሌ: 123456789\n\n"
        "💡 ጓደኛዎን ID ለማወቅ /start ላይ ይጫኑ",
        parse_mode="Markdown"
    )
    await state.set_state(TransferStates.waiting_for_receiver_id)


@dp.message(TransferStates.waiting_for_receiver_id)
async def transfer_receiver_received(message: types.Message, state: FSMContext):
    """User entered receiver telegram ID."""
    try:
        receiver_id = int(message.text.strip())
        sender_id = message.from_user.id
        
        if receiver_id == sender_id:
            await message.answer(
                "❌ ለራስዎ transfer ማድረግ አይችሉም።"
            )
            return
        
        # Verify receiver exists
        try:
            receiver = await api_client.get_user_by_telegram_id(receiver_id)
            if not receiver:
                await message.answer(
                    f"❌ ተጫዋች {receiver_id} አልተገኘም።\n"
                    "እባክዎን ትክክለኛ Telegram ID ያረጋግጡ።"
                )
                return
        except Exception as e:
            await message.answer(
                f"❌ ተጫዋች አልተገኘም። ID ያረጋግጡ።"
            )
            return
        
        # Store receiver info
        await state.update_data(
            receiver_id=receiver_id,
            receiver_name=receiver.get('username') or receiver.get('first_name') or f"Player{receiver_id}"
        )
        
        await message.answer(
            f"✅ ተቀባይ: *{receiver.get('username') or receiver.get('first_name')}*\n\n"
            f"ምን ያህል መጠን ማስተላለፍ ይፈልጋሉ?\n"
            f"ዝቅተኛ: *10 ETB*\n\n"
            f"መጠኑን ያስገቡ (ምሳሌ: 50):",
            parse_mode="Markdown"
        )
        await state.set_state(TransferStates.waiting_for_amount)
        
    except ValueError:
        await message.answer(
            "❌ ትክክለኛ Telegram ID ያስገቡ።\n"
            "ምሳሌ: 123456789"
        )


@dp.message(TransferStates.waiting_for_amount)
async def transfer_amount_received(message: types.Message, state: FSMContext):
    """User entered transfer amount."""
    try:
        amount = float(message.text.strip())
        
        if amount < 10:
            await message.answer(
                "❌ ዝቅተኛ transfer መጠን 10 ETB ነው።"
            )
            return
        
        # Check sender balance
        sender_id = message.from_user.id
        balance_data = await api_client.get_user_balance(sender_id)
        
        if balance_data['balance'] < amount:
            await message.answer(
                f"❌ በቂ ሒሳብ የለዎትም!\n\n"
                f"የጠየቁት: *{amount} ETB*\n"
                f"ያሎት: *{balance_data['balance']} ETB*",
                parse_mode="Markdown"
            )
            return
        
        # Store amount and show confirmation
        data = await state.get_data()
        receiver_name = data.get('receiver_name')
        
        await state.update_data(amount=amount)
        
        await message.answer(
            f"📋 *Transfer መረጃ:*\n\n"
            f"👤 ወደ: *{receiver_name}*\n"
            f"💰 መጠን: *{amount} ETB*\n\n"
            f"ለማረጋገጥ *አዎ* ይላኩ\n"
            f"ለመሰረዝ *ዋጋ* ይላኩ",
            parse_mode="Markdown"
        )
        await state.set_state(TransferStates.waiting_for_confirmation)
        
    except ValueError:
        await message.answer(
            "❌ ትክክለኛ ቁጥር ያስገቡ።"
        )
    except Exception as e:
        logging.error(f"Transfer amount error: {e}")
        await message.answer(
            "❌ ችግር ተፈጥሯል። እባክዎን እንደገና ይሞክሩ።"
        )
        await state.clear()


@dp.message(TransferStates.waiting_for_confirmation)
async def transfer_confirmation_received(message: types.Message, state: FSMContext):
    """User confirmed or cancelled transfer."""
    text = message.text.strip().lower()
    
    if text == "ዋጋ" or text == "cancel":
        await message.answer(
            "❌ Transfer ተሰርዟል።",
            reply_markup=MAIN_MENU
        )
        await state.clear()
        return
    
    if text != "አዎ" and text != "yes":
        await message.answer(
            "እባክዎን *አዎ* ለማረጋገጥ ወይም *ዋጋ* ለመሰረዝ ይላኩ።",
            parse_mode="Markdown"
        )
        return
    
    # User confirmed - send transfer
    data = await state.get_data()
    receiver_id = data.get('receiver_id')
    receiver_name = data.get('receiver_name')
    amount = data.get('amount')
    sender_id = message.from_user.id
    
    try:
        # Send transfer via API
        result = await api_client.send_transfer(
            sender_telegram_id=sender_id,
            receiver_telegram_id=receiver_id,
            amount=amount
        )
        
        await message.answer(
            f"✅ *Transfer ተሳክቷል!*\n\n"
            f"👤 ወደ: *{receiver_name}*\n"
            f"💰 መጠን: *{amount} ETB*\n"
            f"💵 አዲስ ሒሳብ: *{result['sender_new_balance']} ETB*\n\n"
            f"📬 ተቀባዩ notification ተቀብሏል።",
            parse_mode="Markdown",
            reply_markup=MAIN_MENU
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"Transfer execution error: {e}")
        await message.answer(
            f"❌ Transfer አልተሳካም።\n{str(e)}",
            reply_markup=MAIN_MENU
        )
        await state.clear()


# ── Invite ────────────────────────────────────────────────────────────────────
@dp.message(F.text == "🔗 Invite")
async def handle_invite(message: types.Message):
    """Generate referral link for user."""
    bot_info  = await bot.get_me()
    invite_url = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    
    # Get user's referral stats
    try:
        referrals = await api_client.get_referrals(message.from_user.id)
        total_referrals = referrals.get('total_referrals', 0)
        total_earned = referrals.get('total_earned', 0)
        
        await message.answer(
            f"🔗 *ጓደኞቸዎን ይጋብዙ!*\n\n"
            f"📊 *የእርስዎ Statistics:*\n"
            f"👥 Total Invites: *{total_referrals}*\n"
            f"💰 Total Earned: *{total_earned} ETB*\n\n"
            f"🎁 *ለእያንዳንዱ ጓደኛ 5 ETB ያገኛሉ!*\n\n"
            f"ይህን ሊንክ ያጋሩ:\n"
            f"`{invite_url}`\n\n"
            f"📢 ቻናላችንንም ያጋሩ:\n"
            f"{CHANNEL}",
            parse_mode="Markdown",
        )
    except Exception as e:
        # Fallback if API fails
        await message.answer(
            f"🔗 *ጓደኛዎን ይጋብዙ!*\n\n"
            f"🎁 ለእያንዳንዱ ጓደኛ *5 ETB* ያገኛሉ!\n\n"
            f"ይህን ሊንክ ጓደኞቸዎ ያጋሩ:\n\n"
            f"`{invite_url}`\n\n"
            f"📢 ቻናላችንንም ያጋሩ:\n"
            f"{CHANNEL}",
            parse_mode="Markdown",
        )


# ── Convert Bonus ─────────────────────────────────────────────────────────────
@dp.message(F.text == "💱 Convert Bonus")
async def handle_convert_bonus(message: types.Message):
    """
    Convert bonus handler - checks coins via API.
    NOW USES API instead of direct database access! ✅
    """
    telegram_id = message.from_user.id
    
    try:
        # Call FastAPI endpoint (Bot → API → Database)
        balance_data = await api_client.get_user_balance(telegram_id)
        
        if balance_data['coins'] < 100:
            await message.answer(
                f"💲 *Convert Bonus*\n\n"
                f"🪙 ያሎት Coins: *{balance_data['coins']}*\n"
                f"🎮 Play Wallet: *{balance_data['play_balance']:.2f} ETB*\n\n"
                f"❌ ዝቅተኛ conversion: *100 Coins*\n\n"
                f"🎮 ጨዋታ ይጫወቱ coins ይሰብስቡ!",
                parse_mode="Markdown"
            )
            return
        
        # Calculate how much ETB they can get
        max_coins = (balance_data['coins'] // 100) * 100
        etb_amount = max_coins / 100
        
        await message.answer(
            f"💲 *Convert Bonus*\n\n"
            f"🪙 ያሎት Coins: *{balance_data['coins']}*\n"
            f"💱 Conversion Rate: *100 Coins = 1 ETB*\n\n"
            f"✅ ማስተላለፍ የሚችሉት:\n"
            f"🪙 *{max_coins} Coins* → 💵 *{etb_amount} ETB*\n\n"
            f"ለማረጋገጥ ቁጥሩን ይላኩ: *{max_coins}*",
            parse_mode="Markdown"
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


# ── Handle Coin Conversion Amount ─────────────────────────────────────────────
@dp.message(F.text.regexp(r'^\d+$'))
async def handle_conversion_amount(message: types.Message):
    """Handle when user sends a number (for coin conversion)."""
    try:
        coins = int(message.text)
        telegram_id = message.from_user.id
        
        # Check if this is a valid conversion amount
        if coins < 100 or coins % 100 != 0:
            return  # Not a conversion request, ignore
        
        # Try to convert via API
        result = await api_client.convert_bonus(
            telegram_id=telegram_id,
            coins=coins
        )
        
        await message.answer(
            f"✅ *Conversion ተሳክቷል!*\n\n"
            f"🪙 Coins converted: *{result['coins_converted']}*\n"
            f"💵 ETB added: *{result['etb_added']}*\n\n"
            f"📊 *አዲስ Balance:*\n"
            f"🪙 Coins: *{result['new_coins']}*\n"
            f"🎮 Play Wallet: *{result['new_play_balance']:.2f} ETB*",
            parse_mode="Markdown"
        )
        
    except Exception as e:
        # Silently fail if not a conversion (might be other numeric input)
        if "Insufficient coins" in str(e):
            await message.answer(
                "❌ በቂ coins የለዎትም።"
            )
        # Otherwise ignore (might be deposit amount, etc.)


# ── Contact Support ───────────────────────────────────────────────────────────
@dp.message(F.text == "☎️ Contact Support")
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
@dp.message(F.text == "📖 Instruction")
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
@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Cancel any ongoing operation."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("ምንም የሚሰረዝ operation የለም።")
        return
    
    await state.clear()
    await message.answer(
        "❌ Operation ተሰርዟል።",
        reply_markup=MAIN_MENU
    )


@dp.message()
async def catch_all(message: types.Message, state: FSMContext):
    """Catch-all handler - check if in FSM state."""
    current_state = await state.get_state()
    
    if current_state:
        await message.answer(
            "❌ ያልተጠበቀ input።\n"
            "ለመሰረዝ /cancel ይጫኑ።"
        )
    else:
        await message.answer(
            "🤷 ያዘዙትን አላወቅሁም። ከታች ያለውን ሜኑ ይጠቀሙ።",
            reply_markup=MAIN_MENU,
        )


# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    print("🤖 Starting AMHABINGO Telegram Bot...")
    print(f"✅ Using API client: {settings.BACKEND_URL}")
    
    try:
        print("🎯 Bot is now polling for updates...")
        await dp.start_polling(bot)
    finally:
        # Close API client on shutdown
        await api_client.close()
        print("🛑 Bot stopped, API client closed")


if __name__ == "__main__":
    asyncio.run(main())

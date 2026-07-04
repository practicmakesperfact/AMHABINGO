from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List
from ..database import get_db
from ..models import User, Leaderboard, Transaction
from ..schemas import UserResponse, UserCreate, LeaderboardEntry, BonusConvertRequest, BonusConvertResponse
from ..auth import extract_user_from_init_data

router = APIRouter(prefix="/api/users", tags=["users"])


# ─── Register User (for Bot) ──────────────────────────────────────────────────
@router.post("/register", response_model=UserResponse)
async def register_user(
    telegram_id: int,
    phone_number: str,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user via Telegram bot (contact share).
    If user exists, updates phone_number and grants bonus if not already given.
    This endpoint is called by the bot, NOT by the Mini App.
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user:
        # User exists — update phone if missing and give bonus if needed
        if not user.phone_number:
            user.phone_number = phone_number
            
            # Give 10 ETB bonus only if they don't have it yet
            if user.play_balance == 0.0:
                user.play_balance = 10.0
            
            await db.commit()
            await db.refresh(user)
            return user
        else:
            # Already fully registered
            return user
    else:
        # New user — create with phone and 10 ETB play bonus
        user = User(
            telegram_id=telegram_id,
            phone_number=phone_number,
            username=username,
            first_name=first_name,
            last_name=last_name,
            balance=0.0,
            play_balance=10.0,   # FREE BONUS
            coins=0,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


# ─── Get User by Telegram ID ──────────────────────────────────────────────────
@router.get("/by-telegram/{telegram_id}", response_model=UserResponse)
async def get_user_by_telegram_id(telegram_id: int, db: AsyncSession = Depends(get_db)):
    """Get user by telegram_id (for bot operations)."""
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ─── Get User Balance by Telegram ID ──────────────────────────────────────────
@router.get("/by-telegram/{telegram_id}/balance")
async def get_user_balance_by_telegram_id(telegram_id: int, db: AsyncSession = Depends(get_db)):
    """Get balance by telegram_id (for bot operations)."""
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "telegram_id": telegram_id,
        "balance": user.balance,
        "play_balance": user.play_balance,
        "coins": user.coins,
        "total": user.balance + user.play_balance
    }


# ─── Get User Transactions by Telegram ID ─────────────────────────────────────
@router.get("/by-telegram/{telegram_id}/transactions")
async def get_user_transactions_by_telegram_id(
    telegram_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get transaction history by telegram_id (for bot operations)."""
    # Get user
    user_result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get transactions
    txns_result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
    )
    return txns_result.scalars().all()


# ─── Auth / Create User ───────────────────────────────────────────────────────
@router.post("/auth", response_model=UserResponse)
async def authenticate_user(
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate via Telegram initData. Falls back to demo user.
    
    IMPORTANT: Users MUST register via bot (share contact) to get phone_number.
    If user accesses Mini App without bot registration, they're blocked until 
    they complete registration in bot.
    """
    if not init_data:
        # Demo user for local dev
        result = await db.execute(select(User).where(User.telegram_id == 123456789))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=123456789,
                username="demo_user",
                first_name="Demo",
                last_name="Player",
                phone_number="+251900000000",  # Demo phone
                balance=1000.0,
                play_balance=10.0,
                coins=0
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

    user_data = extract_user_from_init_data(init_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")

    telegram_id = user_data.get("id")
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        # Create basic user record but without phone_number and bonus
        # They MUST complete bot registration to get phone + 10 ETB
        user = User(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            phone_number=None,  # Will be set via bot contact share
            balance=0.0,
            play_balance=0.0,   # Will be 10.0 after bot registration
            coins=0
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    # Check if user has completed bot registration
    if not user.phone_number:
        raise HTTPException(
            status_code=403, 
            detail="registration_required",  # Frontend can detect this
            headers={
                "X-Registration-Status": "incomplete",
                "X-Bot-Username": "amhabingo_bot"  # Or from settings
            }
        )

    return user


# ─── Current User ─────────────────────────────────────────────────────────────
@router.get("/me", response_model=UserResponse)
async def get_current_user(
    init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    user_data = extract_user_from_init_data(init_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")

    result = await db.execute(select(User).where(User.telegram_id == user_data["id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ─── Leaderboard ──────────────────────────────────────────────────────────────
@router.get("/leaderboard")
async def get_leaderboard(limit: int = 10, db: AsyncSession = Depends(get_db)):
    """Top players by wins using Redis."""
    from ..redis_client import redis_client
    
    redis_leaders = await redis_client.get_leaderboard(limit)
    
    if redis_leaders:
        user_ids = [int(item[0]) for item in redis_leaders]
        if user_ids:
            result = await db.execute(select(User).where(User.id.in_(user_ids)))
            users_map = {u.id: u for u in result.scalars().all()}
            
            response = []
            for idx, (user_id_str, score) in enumerate(redis_leaders):
                u_id = int(user_id_str)
                u = users_map.get(u_id)
                if u:
                    response.append({
                        "rank": idx + 1,
                        "user_id": u.id,
                        "username": u.username or u.first_name or f"Player{u.id}",
                        "total_wins": int(score),
                        "total_earnings": u.balance,
                    })
            return response

    # Fallback to DB
    result = await db.execute(
        select(User)
        .order_by(desc(User.wins), desc(User.balance))
        .limit(limit)
    )
    users = result.scalars().all()
    return [
        {
            "rank": idx + 1,
            "user_id": u.id,
            "username": u.username or u.first_name or f"Player{u.id}",
            "total_wins": u.wins,
            "total_earnings": u.balance,
        }
        for idx, u in enumerate(users)
    ]


# ─── Get User by ID ───────────────────────────────────────────────────────────
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ─── Get User Balance ─────────────────────────────────────────────────────────
@router.get("/{user_id}/balance")
async def get_user_balance(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "balance": user.balance}


# ─── Platform Stats ───────────────────────────────────────────────────────────
@router.get("/stats/platform")
async def get_platform_stats(db: AsyncSession = Depends(get_db)):
    total_users = await db.scalar(select(func.count(User.id)))
    total_wins = await db.scalar(select(func.sum(User.wins)))
    total_games = await db.scalar(select(func.count()))
    return {
        "activePlayers": total_users or 0,
        "gamesPlayed": total_games or 0,
        "winnersDaily": total_wins or 0,
    }


# ─── Test Deposit (DEV ONLY — remove before production launch!) ───────────────
@router.post("/test-deposit")
async def test_deposit(
    amount: float = 1000.0,
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
):
    """
    Add test balance to a user account.
    ⚠️  FOR TESTING ONLY — remove or protect with admin auth before going live!
    Works with both Telegram users and demo user (no init_data).
    """
    if init_data:
        user_data = extract_user_from_init_data(init_data)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid Telegram data")
        user_result = await db.execute(select(User).where(User.telegram_id == user_data["id"]))
    else:
        user_result = await db.execute(select(User).where(User.telegram_id == 123456789))

    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please authenticate first.")

    user.balance += amount
    await db.commit()
    await db.refresh(user)
    return {
        "message": f"✅ Added {amount} ETB to balance",
        "new_balance": user.balance,
        "play_balance": user.play_balance,
        "user_id": user.id,
        "telegram_id": user.telegram_id,
    }


# ─── User Game History ────────────────────────────────────────────────────────
@router.get("/history")
async def get_user_history(
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db),
):
    """Return last 20 games the authenticated user joined."""
    from ..models import Player, Game

    # Resolve user (support demo mode)
    if not init_data:
        user_result = await db.execute(select(User).where(User.telegram_id == 123456789))
    else:
        user_data = extract_user_from_init_data(init_data)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid Telegram data")
        user_result = await db.execute(select(User).where(User.telegram_id == user_data["id"]))

    user = user_result.scalar_one_or_none()
    if not user:
        return []

    players_result = await db.execute(
        select(Player)
        .where(Player.user_id == user.id)
        .order_by(Player.joined_at.desc())
        .limit(20)
    )
    players = players_result.scalars().all()

    history = []
    for p in players:
        game_result = await db.execute(select(Game).where(Game.id == p.game_id))
        game = game_result.scalar_one_or_none()
        if game:
            history.append({
                "game_id": game.game_id,
                "status": game.status.value,
                "entry_fee": game.entry_fee,
                "prize_pool": game.prize_pool,
                "total_players": game.total_players,
                "card_number": p.card_number,
                "has_won": p.has_won,
                "winning_pattern": p.winning_pattern,
                "joined_at": p.joined_at.isoformat() if p.joined_at else None,
            })
    return history


# ─── Convert Bonus (Coins to ETB) ─────────────────────────────────────────────
@router.post("/bonus/convert", response_model=BonusConvertResponse)
async def convert_bonus(
    request: BonusConvertRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Convert coins to play balance.
    Default rate: 100 coins = 1 ETB play balance.
    For bot operations (telegram_id based).
    """
    from ..config import get_settings
    settings = get_settings()
    
    # Get user by telegram_id
    result = await db.execute(select(User).where(User.telegram_id == request.telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate coin amount
    if request.coins <= 0:
        raise HTTPException(status_code=400, detail="Coins must be positive")
    
    # Minimum conversion: 100 coins
    if request.coins < 100:
        raise HTTPException(status_code=400, detail="Minimum conversion is 100 coins")
    
    # Check if user has enough coins
    if user.coins < request.coins:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient coins. You have {user.coins} coins"
        )
    
    # Calculate conversion (100 coins = 1 ETB)
    conversion_rate = settings.COIN_TO_ETB_RATE  # 100
    etb_amount = request.coins / conversion_rate
    
    # Update user
    user.coins -= request.coins
    user.play_balance += etb_amount
    
    # Create transaction
    transaction = Transaction(
        user_id=user.id,
        type="bonus_conversion",
        amount=etb_amount,
        balance_after=user.play_balance,
        description=f"Converted {request.coins} coins to {etb_amount} ETB",
        reference=f"CONV-{user.id}-{user.created_at.strftime('%Y%m%d%H%M%S')}"
    )
    db.add(transaction)
    
    # Notify user
    from ..models import Notification
    notification = Notification(
        user_id=user.id,
        type="bonus_converted",
        title="Bonus Converted 💲",
        message=f"You converted {request.coins} coins to {etb_amount} ETB play balance!",
        is_read=False
    )
    db.add(notification)
    
    await db.commit()
    await db.refresh(user)
    
    return BonusConvertResponse(
        telegram_id=request.telegram_id,
        coins_converted=request.coins,
        etb_added=etb_amount,
        new_play_balance=user.play_balance,
        new_coins=user.coins,
        conversion_rate=conversion_rate,
        message=f"Successfully converted {request.coins} coins to {etb_amount} ETB"
    )

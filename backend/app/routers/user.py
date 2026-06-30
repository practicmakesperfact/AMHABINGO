from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional, List
from ..database import get_db
from ..models import User, Leaderboard, Transaction
from ..schemas import UserResponse, UserCreate, LeaderboardEntry
from ..auth import extract_user_from_init_data

router = APIRouter(prefix="/api/users", tags=["users"])


# ─── Auth / Create User ───────────────────────────────────────────────────────
@router.post("/auth", response_model=UserResponse)
async def authenticate_user(
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    """Authenticate via Telegram initData. Falls back to demo user."""
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
        user = User(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            balance=0.0,
            play_balance=0.0,  # Given via Bot registration, but 0.0 default here
            coins=0
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

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

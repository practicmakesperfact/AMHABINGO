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
    """Top players by wins."""
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

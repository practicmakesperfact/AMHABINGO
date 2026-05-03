from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from ..database import get_db
from ..models import User
from ..schemas import UserResponse, UserCreate
from ..auth import extract_user_from_init_data

router = APIRouter(prefix="/api/users", tags=["users"])

@router.post("/auth", response_model=UserResponse)
async def authenticate_user(
    init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user via Telegram Web App initData"""
    user_data = extract_user_from_init_data(init_data)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    telegram_id = user_data.get("id")
    
    # Check if user exists
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user
        user = User(
            telegram_id=telegram_id,
            username=user_data.get("username"),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name")
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    """Get current user info"""
    user_data = extract_user_from_init_data(init_data)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    telegram_id = user_data.get("id")
    
    result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

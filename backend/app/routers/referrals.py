"""
Referral API - Referral system with rewards
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from ..database import get_db
from ..models import User, Referral, Transaction, Notification
from ..schemas import ReferralCreate, ReferralResponse
from ..config import get_settings

router = APIRouter(prefix="/api/referrals", tags=["referrals"])
settings = get_settings()


@router.post("/create", response_model=ReferralResponse)
async def create_referral(
    referral_data: ReferralCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a referral record when a new user registers via referral link.
    Pays referrer the referral reward (default: 5 ETB).
    """
    # Get referrer
    referrer_result = await db.execute(
        select(User).where(User.telegram_id == referral_data.referrer_telegram_id)
    )
    referrer = referrer_result.scalar_one_or_none()
    if not referrer:
        raise HTTPException(status_code=404, detail="Referrer not found")

    # Get referee (new user)
    referee_result = await db.execute(
        select(User).where(User.telegram_id == referral_data.referee_telegram_id)
    )
    referee = referee_result.scalar_one_or_none()
    if not referee:
        raise HTTPException(status_code=404, detail="Referee not found")

    # Can't refer yourself
    if referrer.id == referee.id:
        raise HTTPException(status_code=400, detail="Cannot refer yourself")

    # Check if referral already exists
    existing_result = await db.execute(
        select(Referral).where(
            Referral.referrer_id == referrer.id,
            Referral.referee_id == referee.id
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Referral already exists")

    # Create referral record
    referral = Referral(
        referrer_id=referrer.id,
        referee_id=referee.id,
        reward_amount=settings.REFERRAL_REWARD,
        status="completed"
    )
    db.add(referral)

    # Pay referrer reward
    referrer.balance += settings.REFERRAL_REWARD

    # Create transaction
    transaction = Transaction(
        user_id=referrer.id,
        type="referral_reward",
        amount=settings.REFERRAL_REWARD,
        balance_after=referrer.balance,
        description=f"Referral reward for inviting {referee.username or referee.telegram_id}",
        reference=f"REF-{referral.created_at.strftime('%Y%m%d%H%M%S')}"
    )
    db.add(transaction)

    # Notify referrer
    notification = Notification(
        user_id=referrer.id,
        type="referral_reward",
        title="Referral Reward 🎁",
        message=f"You earned {settings.REFERRAL_REWARD} ETB for inviting {referee.first_name or 'a friend'}!",
        is_read=False
    )
    db.add(notification)

    await db.commit()
    await db.refresh(referral)

    return ReferralResponse(
        referral_id=referral.id,
        referrer_telegram_id=referral_data.referrer_telegram_id,
        referee_telegram_id=referral_data.referee_telegram_id,
        reward_amount=settings.REFERRAL_REWARD,
        status=referral.status,
        referrer_new_balance=referrer.balance,
        created_at=referral.created_at,
        message=f"Referral reward of {settings.REFERRAL_REWARD} ETB credited to referrer"
    )


@router.get("/{telegram_id}", response_model=List[dict])
async def get_user_referrals(
    telegram_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all referrals made by a user (users they invited).
    """
    # Get user
    user_result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get referrals where user is referrer
    referrals_result = await db.execute(
        select(Referral)
        .where(Referral.referrer_id == user.id)
        .order_by(Referral.created_at.desc())
    )
    referrals = referrals_result.scalars().all()

    # Format response
    result = []
    for referral in referrals:
        # Get referee details
        referee_result = await db.execute(
            select(User).where(User.id == referral.referee_id)
        )
        referee = referee_result.scalar_one()

        result.append({
            "referral_id": referral.id,
            "referee": {
                "telegram_id": referee.telegram_id,
                "username": referee.username,
                "first_name": referee.first_name
            },
            "reward_amount": referral.reward_amount,
            "status": referral.status,
            "created_at": referral.created_at.isoformat()
        })

    return {
        "total_referrals": len(result),
        "total_earned": sum(r["reward_amount"] for r in result),
        "referrals": result
    }

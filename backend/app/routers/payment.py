"""
Payment router.

All deposits and withdrawals are handled via the Telegram bot (Telebirr).
Only the transaction-history endpoint is kept for the frontend wallet page.
"""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import User, Transaction
from ..auth import extract_user_from_init_data

router = APIRouter(prefix="/api/payment", tags=["payment"])


@router.get("/transactions")
async def get_user_transactions(
    init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    """Return the last 50 transactions for the authenticated user."""
    user_data = extract_user_from_init_data(init_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")

    user_result = await db.execute(select(User).where(User.telegram_id == user_data["id"]))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    txns_result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(50)
    )
    return txns_result.scalars().all()

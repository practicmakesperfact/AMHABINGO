"""
Payment Accounts API - Admin-managed Telebirr accounts for deposits
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from ..database import get_db
from ..models import PaymentAccount, AdminLog, User
from ..schemas import PaymentAccountCreate, PaymentAccountUpdate, PaymentAccountResponse
from ..config import get_settings

router = APIRouter(prefix="/api/payment-accounts", tags=["payment-accounts"])
settings = get_settings()


def is_admin(telegram_id: int) -> bool:
    """Check if user is admin."""
    admin_ids = settings.get_admin_ids()
    return telegram_id in admin_ids


@router.get("", response_model=List[PaymentAccountResponse])
async def get_payment_accounts(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all payment accounts (public endpoint for deposit instructions).
    Returns active accounts by default.
    """
    query = select(PaymentAccount)
    
    if active_only:
        query = query.where(PaymentAccount.is_active == True)
    
    result = await db.execute(query.order_by(PaymentAccount.priority.asc()))
    accounts = result.scalars().all()

    return [
        PaymentAccountResponse(
            id=acc.id,
            account_name=acc.account_name,
            account_holder=acc.account_holder,
            phone_number=acc.phone_number,
            payment_method=acc.payment_method,
            is_active=acc.is_active,
            priority=acc.priority,
            daily_limit=acc.daily_limit,
            notes=acc.notes
        )
        for acc in accounts
    ]


@router.post("", response_model=PaymentAccountResponse)
async def create_payment_account(
    account_data: PaymentAccountCreate,
    admin_telegram_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new payment account (admin only).
    """
    # Check admin authorization
    if not is_admin(admin_telegram_id):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get admin user
    admin_result = await db.execute(
        select(User).where(User.telegram_id == admin_telegram_id)
    )
    admin = admin_result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin user not found")

    # Create account
    account = PaymentAccount(
        account_name=account_data.account_name,
        account_holder=account_data.account_holder,
        phone_number=account_data.phone_number,
        payment_method=account_data.payment_method,
        is_active=account_data.is_active,
        priority=account_data.priority,
        daily_limit=account_data.daily_limit,
        notes=account_data.notes
    )
    db.add(account)

    # Log admin action
    log = AdminLog(
        admin_id=admin.id,
        action="create_payment_account",
        entity_type="PaymentAccount",
        entity_id=None,  # Will update after commit
        details={
            "account_name": account_data.account_name,
            "phone_number": account_data.phone_number
        }
    )
    db.add(log)

    await db.commit()
    await db.refresh(account)

    # Update log with entity_id
    log.entity_id = account.id
    await db.commit()

    return PaymentAccountResponse(
        id=account.id,
        account_name=account.account_name,
        account_holder=account.account_holder,
        phone_number=account.phone_number,
        payment_method=account.payment_method,
        is_active=account.is_active,
        priority=account.priority,
        daily_limit=account.daily_limit,
        notes=account.notes
    )


@router.put("/{account_id}", response_model=PaymentAccountResponse)
async def update_payment_account(
    account_id: int,
    account_data: PaymentAccountUpdate,
    admin_telegram_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a payment account (admin only).
    """
    # Check admin authorization
    if not is_admin(admin_telegram_id):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get admin user
    admin_result = await db.execute(
        select(User).where(User.telegram_id == admin_telegram_id)
    )
    admin = admin_result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin user not found")

    # Get account
    account_result = await db.execute(
        select(PaymentAccount).where(PaymentAccount.id == account_id)
    )
    account = account_result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Payment account not found")

    # Update fields
    update_data = account_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)

    account.updated_at = datetime.utcnow()

    # Log admin action
    log = AdminLog(
        admin_id=admin.id,
        action="update_payment_account",
        entity_type="PaymentAccount",
        entity_id=account.id,
        details={
            "updated_fields": list(update_data.keys()),
            "account_name": account.account_name
        }
    )
    db.add(log)

    await db.commit()
    await db.refresh(account)

    return PaymentAccountResponse(
        id=account.id,
        account_name=account.account_name,
        account_holder=account.account_holder,
        phone_number=account.phone_number,
        payment_method=account.payment_method,
        is_active=account.is_active,
        priority=account.priority,
        daily_limit=account.daily_limit,
        notes=account.notes
    )


@router.delete("/{account_id}")
async def delete_payment_account(
    account_id: int,
    admin_telegram_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a payment account (admin only).
    """
    # Check admin authorization
    if not is_admin(admin_telegram_id):
        raise HTTPException(status_code=403, detail="Admin access required")

    # Get admin user
    admin_result = await db.execute(
        select(User).where(User.telegram_id == admin_telegram_id)
    )
    admin = admin_result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin user not found")

    # Get account
    account_result = await db.execute(
        select(PaymentAccount).where(PaymentAccount.id == account_id)
    )
    account = account_result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Payment account not found")

    # Log admin action
    log = AdminLog(
        admin_id=admin.id,
        action="delete_payment_account",
        entity_type="PaymentAccount",
        entity_id=account.id,
        details={
            "account_name": account.account_name,
            "phone_number": account.phone_number
        }
    )
    db.add(log)

    # Delete account
    await db.delete(account)
    await db.commit()

    return {"message": "Payment account deleted successfully"}

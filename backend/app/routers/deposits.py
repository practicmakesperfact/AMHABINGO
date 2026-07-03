"""
Deposit Management Router
Handles deposit creation, verification, and admin approval.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime
import uuid

from ..database import get_db
from ..models import Deposit, User, DepositStatus, PaymentAccount, PaymentMethod, AdminLog, Notification
from ..config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/deposits", tags=["deposits"])


# ── Helper Functions ──────────────────────────────────────────────────────────

async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> Optional[User]:
    """Get user by telegram_id."""
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


def is_admin(telegram_id: int) -> bool:
    """Check if user is admin."""
    return telegram_id in settings.get_admin_ids()


async def create_notification(
    db: AsyncSession,
    user_id: int,
    type: str,
    title: str,
    message: str,
    action_url: Optional[str] = None
):
    """Create a notification for a user."""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        action_url=action_url
    )
    db.add(notification)


async def log_admin_action(
    db: AsyncSession,
    admin_id: int,
    action: str,
    resource_type: str,
    resource_id: int,
    details: Optional[dict] = None
):
    """Log admin action for audit trail."""
    log = AdminLog(
        admin_id=admin_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {}
    )
    db.add(log)


# ── Create Deposit ────────────────────────────────────────────────────────────

@router.post("/create")
async def create_deposit(
    telegram_id: int,
    amount: float,
    payment_method: str = "telebirr",
    db: AsyncSession = Depends(get_db)
):
    """
    Create a pending deposit request.
    Returns payment instructions and tx_ref.
    """
    # Validate amount
    if amount < settings.MIN_DEPOSIT_AMOUNT:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum deposit is {settings.MIN_DEPOSIT_AMOUNT} ETB"
        )
    
    # Get user
    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get active payment account
    account_result = await db.execute(
        select(PaymentAccount).where(
            and_(
                PaymentAccount.is_active == True,
                PaymentAccount.payment_method == PaymentMethod.TELEBIRR
            )
        ).limit(1)
    )
    account = account_result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=503,
            detail="No payment accounts available. Please contact support."
        )
    
    # Generate unique tx_ref
    tx_ref = f"DEP-{uuid.uuid4().hex[:8].upper()}"
    
    # Create deposit record
    deposit = Deposit(
        user_id=user.id,
        amount=amount,
        payment_method=PaymentMethod.TELEBIRR,
        status=DepositStatus.PENDING,
        tx_ref=tx_ref
    )
    
    db.add(deposit)
    await db.commit()
    await db.refresh(deposit)
    
    return {
        "deposit_id": deposit.id,
        "tx_ref": tx_ref,
        "amount": amount,
        "status": deposit.status.value,
        "payment_instructions": {
            "method": "telebirr",
            "account_number": account.account_number,
            "account_holder": account.account_holder_name,
            "account_name": account.account_name,
            "instructions": [
                f"1. Open Telebirr app",
                f"2. Send {amount} ETB to {account.account_number}",
                f"3. Take screenshot of confirmation",
                f"4. Send screenshot to bot with reference: {tx_ref}"
            ]
        },
        "created_at": deposit.created_at.isoformat()
    }


# ── Verify Deposit (Submit Receipt) ───────────────────────────────────────────

@router.post("/verify")
async def verify_deposit(
    tx_ref: str,
    receipt_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    User submits receipt data for verification.
    Changes status from PENDING to VERIFIED.
    Admin must approve before balance is credited.
    """
    # Get deposit
    result = await db.execute(select(Deposit).where(Deposit.tx_ref == tx_ref))
    deposit = result.scalar_one_or_none()
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    
    if deposit.status != DepositStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Deposit is already {deposit.status.value}"
        )
    
    # Update deposit with receipt data
    deposit.receipt_data = receipt_data
    deposit.receipt_message = receipt_data.get("message", "")
    deposit.status = DepositStatus.VERIFIED
    deposit.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(deposit)
    
    # Notify user
    await create_notification(
        db,
        deposit.user_id,
        "deposit_verified",
        "Deposit Verified",
        f"Your deposit of {deposit.amount} ETB is being reviewed by admin."
    )
    await db.commit()
    
    return {
        "deposit_id": deposit.id,
        "tx_ref": tx_ref,
        "status": deposit.status.value,
        "message": "Receipt submitted. Waiting for admin approval."
    }


# ── Get Pending Deposits (Admin) ──────────────────────────────────────────────

@router.get("/pending")
async def get_pending_deposits(
    admin_telegram_id: int,
    status: Optional[str] = "verified",
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all pending deposits for admin review.
    Only admins can access this endpoint.
    """
    # Check admin
    if not is_admin(admin_telegram_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Build query
    query = select(Deposit).join(User, Deposit.user_id == User.id)
    
    if status:
        if status == "verified":
            query = query.where(Deposit.status == DepositStatus.VERIFIED)
        elif status == "pending":
            query = query.where(Deposit.status == DepositStatus.PENDING)
        elif status == "all":
            query = query.where(Deposit.status.in_([
                DepositStatus.PENDING,
                DepositStatus.VERIFIED
            ]))
    
    query = query.order_by(Deposit.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    deposits = result.scalars().all()
    
    # Format response with user info
    response = []
    for deposit in deposits:
        user_result = await db.execute(select(User).where(User.id == deposit.user_id))
        user = user_result.scalar_one_or_none()
        
        response.append({
            "id": deposit.id,
            "tx_ref": deposit.tx_ref,
            "amount": deposit.amount,
            "status": deposit.status.value,
            "payment_method": deposit.payment_method.value,
            "receipt_data": deposit.receipt_data,
            "receipt_message": deposit.receipt_message,
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "phone_number": user.phone_number
            },
            "created_at": deposit.created_at.isoformat(),
            "updated_at": deposit.updated_at.isoformat() if deposit.updated_at else None
        })
    
    return response


# ── Approve Deposit (Admin) ───────────────────────────────────────────────────

@router.post("/approve")
async def approve_deposit(
    deposit_id: int,
    admin_telegram_id: int,
    notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a deposit and credit user balance.
    Only admins can approve deposits.
    """
    # Check admin
    if not is_admin(admin_telegram_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get admin user
    admin = await get_user_by_telegram_id(db, admin_telegram_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin user not found")
    
    # Get deposit
    result = await db.execute(select(Deposit).where(Deposit.id == deposit_id))
    deposit = result.scalar_one_or_none()
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    
    if deposit.status == DepositStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Deposit already approved")
    
    if deposit.status == DepositStatus.REJECTED:
        raise HTTPException(status_code=400, detail="Deposit was rejected")
    
    # Get user
    user_result = await db.execute(select(User).where(User.id == deposit.user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Credit user balance
    user.balance += deposit.amount
    
    # Update deposit
    deposit.status = DepositStatus.APPROVED
    deposit.admin_id = admin.id
    deposit.admin_notes = notes
    deposit.reviewed_at = datetime.utcnow()
    
    # Log admin action
    await log_admin_action(
        db,
        admin.id,
        "approve_deposit",
        "deposit",
        deposit.id,
        {"amount": deposit.amount, "user_id": user.id}
    )
    
    # Notify user
    await create_notification(
        db,
        user.id,
        "deposit_approved",
        "Deposit Approved ✅",
        f"Your deposit of {deposit.amount} ETB has been approved and credited to your account."
    )
    
    await db.commit()
    await db.refresh(deposit)
    await db.refresh(user)
    
    return {
        "deposit_id": deposit.id,
        "tx_ref": deposit.tx_ref,
        "amount": deposit.amount,
        "status": deposit.status.value,
        "user_id": user.id,
        "new_balance": user.balance,
        "approved_by": admin_telegram_id,
        "reviewed_at": deposit.reviewed_at.isoformat(),
        "message": f"Deposit approved. User balance credited with {deposit.amount} ETB."
    }


# ── Reject Deposit (Admin) ────────────────────────────────────────────────────

@router.post("/reject")
async def reject_deposit(
    deposit_id: int,
    admin_telegram_id: int,
    reason: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Reject a deposit.
    Only admins can reject deposits.
    """
    # Check admin
    if not is_admin(admin_telegram_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get admin user
    admin = await get_user_by_telegram_id(db, admin_telegram_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin user not found")
    
    # Get deposit
    result = await db.execute(select(Deposit).where(Deposit.id == deposit_id))
    deposit = result.scalar_one_or_none()
    
    if not deposit:
        raise HTTPException(status_code=404, detail="Deposit not found")
    
    if deposit.status == DepositStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Cannot reject approved deposit")
    
    if deposit.status == DepositStatus.REJECTED:
        raise HTTPException(status_code=400, detail="Deposit already rejected")
    
    # Update deposit
    deposit.status = DepositStatus.REJECTED
    deposit.admin_id = admin.id
    deposit.admin_notes = reason
    deposit.reviewed_at = datetime.utcnow()
    
    # Log admin action
    await log_admin_action(
        db,
        admin.id,
        "reject_deposit",
        "deposit",
        deposit.id,
        {"amount": deposit.amount, "reason": reason}
    )
    
    # Notify user
    await create_notification(
        db,
        deposit.user_id,
        "deposit_rejected",
        "Deposit Rejected ❌",
        f"Your deposit of {deposit.amount} ETB was rejected. Reason: {reason}"
    )
    
    await db.commit()
    await db.refresh(deposit)
    
    return {
        "deposit_id": deposit.id,
        "tx_ref": deposit.tx_ref,
        "status": deposit.status.value,
        "rejected_by": admin_telegram_id,
        "reason": reason,
        "reviewed_at": deposit.reviewed_at.isoformat(),
        "message": "Deposit rejected."
    }


# ── Get User Deposits ─────────────────────────────────────────────────────────

@router.get("/user/{telegram_id}")
async def get_user_deposits(
    telegram_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get deposit history for a user."""
    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(
        select(Deposit)
        .where(Deposit.user_id == user.id)
        .order_by(Deposit.created_at.desc())
        .limit(limit)
    )
    deposits = result.scalars().all()
    
    return [
        {
            "id": d.id,
            "tx_ref": d.tx_ref,
            "amount": d.amount,
            "status": d.status.value,
            "payment_method": d.payment_method.value,
            "created_at": d.created_at.isoformat(),
            "reviewed_at": d.reviewed_at.isoformat() if d.reviewed_at else None
        }
        for d in deposits
    ]


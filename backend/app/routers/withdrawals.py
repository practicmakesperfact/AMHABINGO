"""
Withdrawal Management Router
Handles withdrawal requests and admin approval.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime
import uuid

from ..database import get_db
from ..models import Withdrawal, User, WithdrawalStatus, PaymentMethod, AdminLog, Notification
from ..config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/withdrawals", tags=["withdrawals"])


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


# ── Request Withdrawal ────────────────────────────────────────────────────────

@router.post("/request")
async def request_withdrawal(
    telegram_id: int,
    amount: float,
    phone_number: str,
    payment_method: str = "telebirr",
    db: AsyncSession = Depends(get_db)
):
    """
    Request a withdrawal.
    Balance is deducted immediately and held until admin approves.
    If rejected, balance is refunded.
    """
    # Validate amount
    if amount < settings.MIN_WITHDRAWAL_AMOUNT:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum withdrawal is {settings.MIN_WITHDRAWAL_AMOUNT} ETB"
        )
    
    # Get user
    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check balance
    if user.balance < amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. You have {user.balance} ETB, need {amount} ETB."
        )
    
    # Generate unique tx_ref
    tx_ref = f"WD-{uuid.uuid4().hex[:8].upper()}"
    
    # Deduct balance immediately (held until approved)
    user.balance -= amount
    
    # Create withdrawal record
    withdrawal = Withdrawal(
        user_id=user.id,
        amount=amount,
        phone_number=phone_number,
        payment_method=PaymentMethod.TELEBIRR,
        status=WithdrawalStatus.PENDING,
        tx_ref=tx_ref
    )
    
    db.add(withdrawal)
    
    # Notify user
    await create_notification(
        db,
        user.id,
        "withdrawal_requested",
        "Withdrawal Requested",
        f"Your withdrawal request for {amount} ETB is pending admin approval."
    )
    
    await db.commit()
    await db.refresh(withdrawal)
    await db.refresh(user)
    
    return {
        "withdrawal_id": withdrawal.id,
        "tx_ref": tx_ref,
        "amount": amount,
        "phone_number": phone_number,
        "status": withdrawal.status.value,
        "new_balance": user.balance,
        "message": "Withdrawal request submitted. Funds are held until admin approval.",
        "created_at": withdrawal.created_at.isoformat()
    }


# ── Get Pending Withdrawals (Admin) ───────────────────────────────────────────

@router.get("/pending")
async def get_pending_withdrawals(
    admin_telegram_id: int,
    status: Optional[str] = "pending",
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all pending withdrawals for admin review.
    Only admins can access this endpoint.
    """
    # Check admin
    if not is_admin(admin_telegram_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Build query
    query = select(Withdrawal).join(User, Withdrawal.user_id == User.id)
    
    if status:
        if status == "pending":
            query = query.where(Withdrawal.status == WithdrawalStatus.PENDING)
        elif status == "processing":
            query = query.where(Withdrawal.status == WithdrawalStatus.PROCESSING)
        elif status == "all":
            query = query.where(Withdrawal.status.in_([
                WithdrawalStatus.PENDING,
                WithdrawalStatus.PROCESSING
            ]))
    
    query = query.order_by(Withdrawal.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    withdrawals = result.scalars().all()
    
    # Format response with user info
    response = []
    for withdrawal in withdrawals:
        user_result = await db.execute(select(User).where(User.id == withdrawal.user_id))
        user = user_result.scalar_one_or_none()
        
        response.append({
            "id": withdrawal.id,
            "tx_ref": withdrawal.tx_ref,
            "amount": withdrawal.amount,
            "phone_number": withdrawal.phone_number,
            "status": withdrawal.status.value,
            "payment_method": withdrawal.payment_method.value,
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "phone_number": user.phone_number,
                "current_balance": user.balance
            },
            "created_at": withdrawal.created_at.isoformat(),
            "updated_at": withdrawal.updated_at.isoformat() if withdrawal.updated_at else None
        })
    
    return response


# ── Approve Withdrawal (Admin) ────────────────────────────────────────────────

@router.post("/approve")
async def approve_withdrawal(
    withdrawal_id: int,
    admin_telegram_id: int,
    notes: Optional[str] = None,
    payment_proof: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve a withdrawal and process payment.
    Only admins can approve withdrawals.
    """
    # Check admin
    if not is_admin(admin_telegram_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get admin user
    admin = await get_user_by_telegram_id(db, admin_telegram_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin user not found")
    
    # Get withdrawal
    result = await db.execute(select(Withdrawal).where(Withdrawal.id == withdrawal_id))
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal.status == WithdrawalStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Withdrawal already approved")
    
    if withdrawal.status == WithdrawalStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Withdrawal already completed")
    
    if withdrawal.status == WithdrawalStatus.REJECTED:
        raise HTTPException(status_code=400, detail="Withdrawal was rejected")
    
    # Get user
    user_result = await db.execute(select(User).where(User.id == withdrawal.user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update withdrawal
    withdrawal.status = WithdrawalStatus.APPROVED
    withdrawal.admin_id = admin.id
    withdrawal.admin_notes = notes
    withdrawal.payment_proof = payment_proof
    withdrawal.reviewed_at = datetime.utcnow()
    
    # Log admin action
    await log_admin_action(
        db,
        admin.id,
        "approve_withdrawal",
        "withdrawal",
        withdrawal.id,
        {"amount": withdrawal.amount, "user_id": user.id, "phone": withdrawal.phone_number}
    )
    
    # Notify user
    await create_notification(
        db,
        user.id,
        "withdrawal_approved",
        "Withdrawal Approved ✅",
        f"Your withdrawal of {withdrawal.amount} ETB to {withdrawal.phone_number} has been approved and is being processed."
    )
    
    await db.commit()
    await db.refresh(withdrawal)
    
    return {
        "withdrawal_id": withdrawal.id,
        "tx_ref": withdrawal.tx_ref,
        "amount": withdrawal.amount,
        "phone_number": withdrawal.phone_number,
        "status": withdrawal.status.value,
        "user_id": user.id,
        "approved_by": admin_telegram_id,
        "reviewed_at": withdrawal.reviewed_at.isoformat(),
        "message": f"Withdrawal approved. Payment of {withdrawal.amount} ETB will be sent to {withdrawal.phone_number}."
    }


# ── Mark Withdrawal as Completed (Admin) ──────────────────────────────────────

@router.post("/complete")
async def complete_withdrawal(
    withdrawal_id: int,
    admin_telegram_id: int,
    payment_proof: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark withdrawal as completed after payment is sent.
    Only admins can mark as completed.
    """
    # Check admin
    if not is_admin(admin_telegram_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get admin user
    admin = await get_user_by_telegram_id(db, admin_telegram_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin user not found")
    
    # Get withdrawal
    result = await db.execute(select(Withdrawal).where(Withdrawal.id == withdrawal_id))
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal.status != WithdrawalStatus.APPROVED:
        raise HTTPException(status_code=400, detail="Withdrawal must be approved first")
    
    # Update withdrawal
    withdrawal.status = WithdrawalStatus.COMPLETED
    withdrawal.payment_proof = payment_proof
    withdrawal.completed_at = datetime.utcnow()
    
    # Log admin action
    await log_admin_action(
        db,
        admin.id,
        "complete_withdrawal",
        "withdrawal",
        withdrawal.id,
        {"amount": withdrawal.amount, "payment_proof": payment_proof}
    )
    
    # Notify user
    await create_notification(
        db,
        withdrawal.user_id,
        "withdrawal_completed",
        "Withdrawal Completed ✅",
        f"Your withdrawal of {withdrawal.amount} ETB has been sent to {withdrawal.phone_number}."
    )
    
    await db.commit()
    await db.refresh(withdrawal)
    
    return {
        "withdrawal_id": withdrawal.id,
        "tx_ref": withdrawal.tx_ref,
        "status": withdrawal.status.value,
        "completed_at": withdrawal.completed_at.isoformat(),
        "message": "Withdrawal marked as completed."
    }


# ── Reject Withdrawal (Admin) ─────────────────────────────────────────────────

@router.post("/reject")
async def reject_withdrawal(
    withdrawal_id: int,
    admin_telegram_id: int,
    reason: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Reject a withdrawal and refund user balance.
    Only admins can reject withdrawals.
    """
    # Check admin
    if not is_admin(admin_telegram_id):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get admin user
    admin = await get_user_by_telegram_id(db, admin_telegram_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin user not found")
    
    # Get withdrawal
    result = await db.execute(select(Withdrawal).where(Withdrawal.id == withdrawal_id))
    withdrawal = result.scalar_one_or_none()
    
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    
    if withdrawal.status == WithdrawalStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot reject completed withdrawal")
    
    if withdrawal.status == WithdrawalStatus.REJECTED:
        raise HTTPException(status_code=400, detail="Withdrawal already rejected")
    
    # Get user
    user_result = await db.execute(select(User).where(User.id == withdrawal.user_id))
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Refund balance (was deducted when withdrawal was requested)
    user.balance += withdrawal.amount
    
    # Update withdrawal
    withdrawal.status = WithdrawalStatus.REJECTED
    withdrawal.admin_id = admin.id
    withdrawal.admin_notes = reason
    withdrawal.reviewed_at = datetime.utcnow()
    
    # Log admin action
    await log_admin_action(
        db,
        admin.id,
        "reject_withdrawal",
        "withdrawal",
        withdrawal.id,
        {"amount": withdrawal.amount, "reason": reason, "refunded": True}
    )
    
    # Notify user
    await create_notification(
        db,
        user.id,
        "withdrawal_rejected",
        "Withdrawal Rejected ❌",
        f"Your withdrawal of {withdrawal.amount} ETB was rejected. Reason: {reason}. Balance has been refunded."
    )
    
    await db.commit()
    await db.refresh(withdrawal)
    await db.refresh(user)
    
    return {
        "withdrawal_id": withdrawal.id,
        "tx_ref": withdrawal.tx_ref,
        "status": withdrawal.status.value,
        "rejected_by": admin_telegram_id,
        "reason": reason,
        "refunded_amount": withdrawal.amount,
        "new_balance": user.balance,
        "reviewed_at": withdrawal.reviewed_at.isoformat(),
        "message": f"Withdrawal rejected. {withdrawal.amount} ETB refunded to user balance."
    }


# ── Get User Withdrawals ──────────────────────────────────────────────────────

@router.get("/user/{telegram_id}")
async def get_user_withdrawals(
    telegram_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """Get withdrawal history for a user."""
    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = await db.execute(
        select(Withdrawal)
        .where(Withdrawal.user_id == user.id)
        .order_by(Withdrawal.created_at.desc())
        .limit(limit)
    )
    withdrawals = result.scalars().all()
    
    return [
        {
            "id": w.id,
            "tx_ref": w.tx_ref,
            "amount": w.amount,
            "phone_number": w.phone_number,
            "status": w.status.value,
            "payment_method": w.payment_method.value,
            "created_at": w.created_at.isoformat(),
            "reviewed_at": w.reviewed_at.isoformat() if w.reviewed_at else None,
            "completed_at": w.completed_at.isoformat() if w.completed_at else None
        }
        for w in withdrawals
    ]


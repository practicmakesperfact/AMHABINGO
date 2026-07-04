"""
Transfer API - User-to-user money transfers
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from ..database import get_db
from ..models import User, Transfer, Transaction, Notification
from ..schemas import TransferCreate, TransferResponse
from ..config import get_settings

router = APIRouter(prefix="/api/transfers", tags=["transfers"])
settings = get_settings()


@router.post("/send", response_model=TransferResponse)
async def send_transfer(
    transfer_data: TransferCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Send money to another user (instant transfer).
    Validates sender balance and deducts immediately.
    """
    # Get sender
    sender_result = await db.execute(
        select(User).where(User.telegram_id == transfer_data.sender_telegram_id)
    )
    sender = sender_result.scalar_one_or_none()
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")

    # Get receiver
    receiver_result = await db.execute(
        select(User).where(User.telegram_id == transfer_data.receiver_telegram_id)
    )
    receiver = receiver_result.scalar_one_or_none()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    # Validate amount
    if transfer_data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    if transfer_data.amount < 10:
        raise HTTPException(status_code=400, detail="Minimum transfer amount is 10 ETB")

    # Check sender balance
    if sender.balance < transfer_data.amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. You have {sender.balance} ETB"
        )

    # Can't transfer to yourself
    if sender.id == receiver.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to yourself")

    # Create transfer record
    transfer = Transfer(
        sender_id=sender.id,
        receiver_id=receiver.id,
        amount=transfer_data.amount,
        status="completed",
        notes=transfer_data.notes
    )
    db.add(transfer)

    # Update balances
    sender.balance -= transfer_data.amount
    receiver.balance += transfer_data.amount

    # Create transaction records for both users
    sender_tx = Transaction(
        user_id=sender.id,
        type="transfer_out",
        amount=-transfer_data.amount,
        balance_after=sender.balance,
        description=f"Transfer to {receiver.username or receiver.telegram_id}",
        reference=f"TRANS-{transfer.created_at.strftime('%Y%m%d%H%M%S')}"
    )
    
    receiver_tx = Transaction(
        user_id=receiver.id,
        type="transfer_in",
        amount=transfer_data.amount,
        balance_after=receiver.balance,
        description=f"Transfer from {sender.username or sender.telegram_id}",
        reference=f"TRANS-{transfer.created_at.strftime('%Y%m%d%H%M%S')}"
    )
    
    db.add(sender_tx)
    db.add(receiver_tx)

    # Notify both users
    sender_notif = Notification(
        user_id=sender.id,
        type="transfer_sent",
        title="Transfer Sent ✅",
        message=f"You sent {transfer_data.amount} ETB to {receiver.username or 'user'}",
        is_read=False
    )
    
    receiver_notif = Notification(
        user_id=receiver.id,
        type="transfer_received",
        title="Money Received 💰",
        message=f"You received {transfer_data.amount} ETB from {sender.username or 'user'}",
        is_read=False
    )
    
    db.add(sender_notif)
    db.add(receiver_notif)

    await db.commit()
    await db.refresh(transfer)

    return TransferResponse(
        transfer_id=transfer.id,
        sender_telegram_id=transfer_data.sender_telegram_id,
        receiver_telegram_id=transfer_data.receiver_telegram_id,
        amount=transfer_data.amount,
        status=transfer.status,
        sender_new_balance=sender.balance,
        receiver_new_balance=receiver.balance,
        created_at=transfer.created_at,
        message=f"Successfully transferred {transfer_data.amount} ETB"
    )


@router.get("/user/{telegram_id}", response_model=List[dict])
async def get_user_transfers(
    telegram_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get transfer history for a user (both sent and received).
    """
    # Get user
    user_result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get transfers where user is sender or receiver
    transfers_result = await db.execute(
        select(Transfer)
        .where(
            (Transfer.sender_id == user.id) | (Transfer.receiver_id == user.id)
        )
        .order_by(Transfer.created_at.desc())
        .limit(limit)
    )
    transfers = transfers_result.scalars().all()

    # Format response
    result = []
    for transfer in transfers:
        # Get sender and receiver details
        sender_result = await db.execute(
            select(User).where(User.id == transfer.sender_id)
        )
        sender = sender_result.scalar_one()
        
        receiver_result = await db.execute(
            select(User).where(User.id == transfer.receiver_id)
        )
        receiver = receiver_result.scalar_one()

        result.append({
            "transfer_id": transfer.id,
            "amount": transfer.amount,
            "direction": "sent" if transfer.sender_id == user.id else "received",
            "other_user": {
                "telegram_id": receiver.telegram_id if transfer.sender_id == user.id else sender.telegram_id,
                "username": receiver.username if transfer.sender_id == user.id else sender.username,
                "first_name": receiver.first_name if transfer.sender_id == user.id else sender.first_name
            },
            "status": transfer.status,
            "notes": transfer.notes,
            "created_at": transfer.created_at.isoformat()
        })

    return result

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import User, Game, Transaction, TransactionStatus, TransactionType
from ..schemas import PaymentInitRequest, PaymentInitResponse, PaymentVerifyRequest
from ..auth import extract_user_from_init_data
from ..payment import payment_service

router = APIRouter(prefix="/api/payments", tags=["payments"])

@router.post("/initialize", response_model=PaymentInitResponse)
async def initialize_payment(
    payment_data: PaymentInitRequest,
    init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    """Initialize payment for joining a game"""
    user_data = extract_user_from_init_data(init_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    telegram_id = user_data.get("id")
    
    # Get user
    user_result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get game
    game_result = await db.execute(
        select(Game).where(Game.game_id == payment_data.game_id)
    )
    game = game_result.scalar_one_or_none()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Generate transaction reference
    tx_ref = payment_service.generate_tx_ref(user.id, payment_data.game_id)
    
    # Create transaction record
    transaction = Transaction(
        user_id=user.id,
        game_id=game.id,
        amount=game.entry_fee,
        tx_ref=tx_ref,
        status=TransactionStatus.PENDING,
        type=TransactionType.ENTRY_FEE,
        metadata={
            "game_id": payment_data.game_id,
            "card_number": payment_data.card_number
        }
    )
    
    db.add(transaction)
    await db.commit()
    
    # Initialize payment with Chapa
    email = f"player.{user.telegram_id}@amhabingo.et"
    callback_url = "https://your-frontend-url.com/payment/callback"
    return_url = f"https://your-frontend-url.com/game/{payment_data.game_id}"
    
    result = await payment_service.initialize_payment(
        amount=game.entry_fee,
        email=email,
        first_name=user.first_name or "Player",
        last_name=user.last_name or str(user.telegram_id),
        tx_ref=tx_ref,
        callback_url=callback_url,
        return_url=return_url
    )
    
    if result.get("status") != "success":
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Payment initialization failed")
        )
    
    checkout_url = result["data"]["checkout_url"]
    
    return PaymentInitResponse(
        checkout_url=checkout_url,
        tx_ref=tx_ref
    )

@router.post("/verify")
async def verify_payment(
    verify_data: PaymentVerifyRequest,
    init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    """Verify payment status"""
    user_data = extract_user_from_init_data(init_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    # Get transaction
    result = await db.execute(
        select(Transaction).where(Transaction.tx_ref == verify_data.tx_ref)
    )
    transaction = result.scalar_one_or_none()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Verify with Chapa
    payment_status = await payment_service.get_payment_status(verify_data.tx_ref)
    
    if payment_status == "success":
        transaction.status = TransactionStatus.SUCCESS
        await db.commit()
        
        return {
            "status": "success",
            "message": "Payment verified successfully",
            "transaction": {
                "tx_ref": transaction.tx_ref,
                "amount": transaction.amount,
                "status": transaction.status.value
            }
        }
    elif payment_status == "pending":
        return {
            "status": "pending",
            "message": "Payment is still pending"
        }
    else:
        transaction.status = TransactionStatus.FAILED
        await db.commit()
        
        return {
            "status": "failed",
            "message": "Payment verification failed"
        }

@router.get("/transactions")
async def get_user_transactions(
    init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    """Get user's transaction history"""
    user_data = extract_user_from_init_data(init_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    telegram_id = user_data.get("id")
    
    # Get user
    user_result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get transactions
    transactions_result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.created_at.desc())
        .limit(50)
    )
    transactions = transactions_result.scalars().all()
    
    return transactions

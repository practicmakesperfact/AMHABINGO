from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..database import get_db
from ..models import User, Game, Transaction, TransactionStatus, TransactionType
from ..schemas import PaymentInitRequest, PaymentInitResponse, PaymentVerifyRequest
from ..auth import extract_user_from_init_data
from ..payment import payment_service
from ..config import get_settings

router = APIRouter(prefix="/api/payment", tags=["payment"])
settings = get_settings()


@router.post("/initialize", response_model=PaymentInitResponse)
async def initialize_payment(
    payment_data: PaymentInitRequest,
    init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    """Initialize Chapa payment for joining a game."""
    user_data = extract_user_from_init_data(init_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")

    user_result = await db.execute(select(User).where(User.telegram_id == user_data["id"]))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    game_result = await db.execute(select(Game).where(Game.game_id == payment_data.game_id))
    game = game_result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    tx_ref = payment_service.generate_tx_ref(user.id, payment_data.game_id)

    transaction = Transaction(
        user_id=user.id,
        game_id=game.id,
        amount=game.entry_fee,
        tx_ref=tx_ref,
        status=TransactionStatus.PENDING,
        type=TransactionType.ENTRY_FEE,
        extra_data={                         # ← fixed: was metadata
            "game_id": payment_data.game_id,
            "card_number": payment_data.card_number
        }
    )
    db.add(transaction)
    await db.commit()

    frontend_url = settings.FRONTEND_URL
    result = await payment_service.initialize_payment(
        amount=game.entry_fee,
        email=f"player.{user.telegram_id}@amhabingo.et",
        first_name=user.first_name or "Player",
        last_name=user.last_name or str(user.telegram_id),
        tx_ref=tx_ref,
        callback_url=f"{frontend_url}/payment/callback",
        return_url=f"{frontend_url}/game/{payment_data.game_id}"
    )

    if result.get("status") != "success":
        raise HTTPException(status_code=400, detail=result.get("message", "Payment init failed"))

    return PaymentInitResponse(
        checkout_url=result["data"]["checkout_url"],
        tx_ref=tx_ref
    )


@router.post("/verify")
async def verify_payment(
    verify_data: PaymentVerifyRequest,
    init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    user_data = extract_user_from_init_data(init_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")

    result = await db.execute(select(Transaction).where(Transaction.tx_ref == verify_data.tx_ref))
    transaction = result.scalar_one_or_none()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    payment_status = await payment_service.get_payment_status(verify_data.tx_ref)

    if payment_status == "success":
        transaction.status = TransactionStatus.SUCCESS
        await db.commit()
        return {"status": "success", "tx_ref": transaction.tx_ref, "amount": transaction.amount}
    elif payment_status == "pending":
        return {"status": "pending", "message": "Payment still pending"}
    else:
        transaction.status = TransactionStatus.FAILED
        await db.commit()
        return {"status": "failed", "message": "Payment failed"}


@router.get("/transactions")
async def get_user_transactions(
    init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
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

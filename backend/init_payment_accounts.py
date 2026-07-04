"""
Initialize Payment Accounts
Adds default Telebirr account for deposits.
"""

import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import PaymentAccount


async def init_payment_accounts():
    """Initialize default payment accounts."""
    async with AsyncSessionLocal() as db:
        # Check if accounts already exist
        result = await db.execute(select(PaymentAccount))
        existing = result.scalars().all()
        
        if existing:
            print(f"✅ Payment accounts already exist ({len(existing)} accounts)")
            for acc in existing:
                print(f"   - {acc.account_name}: {acc.phone_number}")
            return
        
        # Create default account
        account = PaymentAccount(
            account_name="AMHABINGO Official",
            account_holder="AMHABINGO Support",
            phone_number="+251909425014",  # Your phone number
            payment_method="telebirr",
            is_active=True,
            priority=1,
            daily_limit=100000.0,  # 100,000 ETB daily limit
            notes="Primary deposit account"
        )
        
        db.add(account)
        await db.commit()
        await db.refresh(account)
        
        print("✅ Payment account created successfully!")
        print(f"   Account Name: {account.account_name}")
        print(f"   Phone Number: {account.phone_number}")
        print(f"   Account Holder: {account.account_holder}")
        print(f"   Status: {'Active' if account.is_active else 'Inactive'}")


if __name__ == "__main__":
    print("🏦 Initializing payment accounts...")
    asyncio.run(init_payment_accounts())
    print("✨ Done!")

"""
Bot API Client - HTTP client for Telegram Bot to communicate with FastAPI backend.
This ensures the bot NEVER directly accesses the database.

Bot → BotAPIClient (HTTP) → FastAPI → Database
"""

import httpx
from typing import Optional, Dict, List
from app.config import get_settings

settings = get_settings()


class BotAPIClient:
    """
    HTTP client for the Telegram bot to interact with FastAPI backend.
    All bot operations MUST go through this client.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True
        )

    async def close(self):
        """Close the HTTP client connection."""
        await self.client.aclose()

    # ── User Operations ───────────────────────────────────────────────────────

    async def register_user(
        self,
        telegram_id: int,
        phone_number: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None
    ) -> Dict:
        """
        Register a new user or update existing user with phone number.
        Returns user data with balance, play_balance, etc.
        """
        response = await self.client.post(
            f"{self.base_url}/api/users/register",
            json={
                "telegram_id": telegram_id,
                "phone_number": phone_number,
                "username": username,
                "first_name": first_name,
                "last_name": last_name
            }
        )
        response.raise_for_status()
        return response.json()

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Get user by telegram_id."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/users/by-telegram/{telegram_id}"
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def get_user_balance(self, telegram_id: int) -> Dict:
        """Get user balance (main wallet + play wallet)."""
        response = await self.client.get(
            f"{self.base_url}/api/users/by-telegram/{telegram_id}/balance"
        )
        response.raise_for_status()
        return response.json()

    # ── Deposit Operations ────────────────────────────────────────────────────

    async def create_deposit(
        self,
        telegram_id: int,
        amount: float,
        payment_method: str = "telebirr"
    ) -> Dict:
        """
        Create a pending deposit request.
        Returns deposit record with tx_ref and payment instructions.
        """
        response = await self.client.post(
            f"{self.base_url}/api/deposits/create",
            json={
                "telegram_id": telegram_id,
                "amount": amount,
                "payment_method": payment_method
            }
        )
        response.raise_for_status()
        return response.json()

    async def verify_deposit(
        self,
        tx_ref: str,
        receipt_data: Dict
    ) -> Dict:
        """
        Submit deposit receipt for verification.
        Admin must approve before balance is credited.
        """
        response = await self.client.post(
            f"{self.base_url}/api/deposits/verify",
            json={
                "tx_ref": tx_ref,
                "receipt_data": receipt_data
            }
        )
        response.raise_for_status()
        return response.json()

    async def get_pending_deposits(self, admin_id: Optional[int] = None) -> List[Dict]:
        """Get all pending deposits (admin only)."""
        params = {}
        if admin_id:
            params["admin_id"] = admin_id

        response = await self.client.get(
            f"{self.base_url}/api/deposits/pending",
            params=params
        )
        response.raise_for_status()
        return response.json()

    async def approve_deposit(
        self,
        deposit_id: int,
        admin_telegram_id: int,
        notes: Optional[str] = None
    ) -> Dict:
        """Approve a deposit (admin only). Credits user balance."""
        response = await self.client.post(
            f"{self.base_url}/api/deposits/approve",
            json={
                "deposit_id": deposit_id,
                "admin_telegram_id": admin_telegram_id,
                "notes": notes
            }
        )
        response.raise_for_status()
        return response.json()

    async def reject_deposit(
        self,
        deposit_id: int,
        admin_telegram_id: int,
        reason: str
    ) -> Dict:
        """Reject a deposit (admin only)."""
        response = await self.client.post(
            f"{self.base_url}/api/deposits/reject",
            json={
                "deposit_id": deposit_id,
                "admin_telegram_id": admin_telegram_id,
                "reason": reason
            }
        )
        response.raise_for_status()
        return response.json()

    # ── Withdrawal Operations ─────────────────────────────────────────────────

    async def request_withdrawal(
        self,
        telegram_id: int,
        amount: float,
        phone_number: str,
        payment_method: str = "telebirr"
    ) -> Dict:
        """
        Request a withdrawal. Requires admin approval.
        Balance is deducted immediately but held until approved.
        """
        response = await self.client.post(
            f"{self.base_url}/api/withdrawals/request",
            json={
                "telegram_id": telegram_id,
                "amount": amount,
                "phone_number": phone_number,
                "payment_method": payment_method
            }
        )
        response.raise_for_status()
        return response.json()

    async def get_pending_withdrawals(self, admin_id: Optional[int] = None) -> List[Dict]:
        """Get all pending withdrawals (admin only)."""
        params = {}
        if admin_id:
            params["admin_id"] = admin_id

        response = await self.client.get(
            f"{self.base_url}/api/withdrawals/pending",
            params=params
        )
        response.raise_for_status()
        return response.json()

    async def approve_withdrawal(
        self,
        withdrawal_id: int,
        admin_telegram_id: int,
        notes: Optional[str] = None
    ) -> Dict:
        """Approve a withdrawal (admin only). Processes payment."""
        response = await self.client.post(
            f"{self.base_url}/api/withdrawals/approve",
            json={
                "withdrawal_id": withdrawal_id,
                "admin_telegram_id": admin_telegram_id,
                "notes": notes
            }
        )
        response.raise_for_status()
        return response.json()

    async def reject_withdrawal(
        self,
        withdrawal_id: int,
        admin_telegram_id: int,
        reason: str
    ) -> Dict:
        """Reject a withdrawal (admin only). Refunds balance."""
        response = await self.client.post(
            f"{self.base_url}/api/withdrawals/reject",
            json={
                "withdrawal_id": withdrawal_id,
                "admin_telegram_id": admin_telegram_id,
                "reason": reason
            }
        )
        response.raise_for_status()
        return response.json()

    # ── Transfer Operations ───────────────────────────────────────────────────

    async def send_transfer(
        self,
        sender_telegram_id: int,
        receiver_telegram_id: int,
        amount: float
    ) -> Dict:
        """Transfer balance from one user to another."""
        response = await self.client.post(
            f"{self.base_url}/api/transfers/send",
            json={
                "sender_telegram_id": sender_telegram_id,
                "receiver_telegram_id": receiver_telegram_id,
                "amount": amount
            }
        )
        response.raise_for_status()
        return response.json()

    # ── Referral Operations ───────────────────────────────────────────────────

    async def create_referral(
        self,
        referrer_telegram_id: int,
        referee_telegram_id: int
    ) -> Dict:
        """Create a referral record and reward referrer."""
        response = await self.client.post(
            f"{self.base_url}/api/referrals/create",
            json={
                "referrer_telegram_id": referrer_telegram_id,
                "referee_telegram_id": referee_telegram_id
            }
        )
        response.raise_for_status()
        return response.json()

    async def get_referrals(self, telegram_id: int) -> List[Dict]:
        """Get all referrals for a user."""
        response = await self.client.get(
            f"{self.base_url}/api/referrals/{telegram_id}"
        )
        response.raise_for_status()
        return response.json()

    # ── Bonus Operations ──────────────────────────────────────────────────────

    async def convert_bonus(
        self,
        telegram_id: int,
        coins: int
    ) -> Dict:
        """
        Convert coins to play balance.
        Typically: 100 coins = 1 ETB play balance.
        """
        response = await self.client.post(
            f"{self.base_url}/api/bonus/convert",
            json={
                "telegram_id": telegram_id,
                "coins": coins
            }
        )
        response.raise_for_status()
        return response.json()

    # ── Payment Accounts ──────────────────────────────────────────────────────

    async def get_payment_accounts(self) -> List[Dict]:
        """Get active Telebirr accounts for deposits."""
        response = await self.client.get(
            f"{self.base_url}/api/payment-accounts"
        )
        response.raise_for_status()
        return response.json()

    # ── Admin Operations ──────────────────────────────────────────────────────

    async def broadcast_message(
        self,
        admin_telegram_id: int,
        message: str,
        target: str = "all"  # all, active_players, winners
    ) -> Dict:
        """Broadcast a message to users (admin only)."""
        response = await self.client.post(
            f"{self.base_url}/api/admin/broadcast",
            json={
                "admin_telegram_id": admin_telegram_id,
                "message": message,
                "target": target
            }
        )
        response.raise_for_status()
        return response.json()

    async def get_admin_stats(self, admin_telegram_id: int) -> Dict:
        """Get admin dashboard statistics."""
        response = await self.client.get(
            f"{self.base_url}/api/admin/stats",
            params={"admin_telegram_id": admin_telegram_id}
        )
        response.raise_for_status()
        return response.json()

    # ── Transaction History ───────────────────────────────────────────────────

    async def get_transactions(
        self,
        telegram_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """Get transaction history for a user."""
        response = await self.client.get(
            f"{self.base_url}/api/users/by-telegram/{telegram_id}/transactions",
            params={"limit": limit}
        )
        response.raise_for_status()
        return response.json()


# ── Singleton instance ────────────────────────────────────────────────────────

# Initialize with backend URL from settings
# Bot will use this instance for all API calls
api_client = BotAPIClient(settings.FRONTEND_URL.replace("3000", "8000"))  # Adjust port for backend


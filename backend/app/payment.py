import httpx
import uuid
from typing import Dict, Any
from .config import get_settings

settings = get_settings()

class ChapaPayment:
    """Chapa payment integration"""
    
    def __init__(self):
        self.secret_key = settings.CHAPA_SECRET_KEY
        self.base_url = "https://api.chapa.co/v1"
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
    
    def generate_tx_ref(self, user_id: int, game_id: str) -> str:
        """Generate unique transaction reference"""
        return f"AMHA-{game_id}-{user_id}-{uuid.uuid4().hex[:8]}"
    
    async def initialize_payment(
        self,
        amount: float,
        email: str,
        first_name: str,
        last_name: str,
        tx_ref: str,
        callback_url: str,
        return_url: str
    ) -> Dict[str, Any]:
        """
        Initialize payment with Chapa
        
        Returns:
            {
                "status": "success",
                "message": "Hosted Link",
                "data": {
                    "checkout_url": "https://checkout.chapa.co/..."
                }
            }
        """
        payload = {
            "amount": str(amount),
            "currency": "ETB",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": tx_ref,
            "callback_url": callback_url,
            "return_url": return_url,
            "customization": {
                "title": "AMHABINGO",
                "description": "Bingo game entry fee"
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/transaction/initialize",
                    json=payload,
                    headers=self.headers,
                    timeout=30.0
                )
                result = response.json()
                
                if result.get("status") != "success":
                    print(f"Chapa initialization error: {result}")
                
                return result
        except Exception as e:
            print(f"Payment initialization exception: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def verify_payment(self, tx_ref: str) -> Dict[str, Any]:
        """
        Verify payment transaction
        
        Returns:
            {
                "status": "success",
                "message": "Payment details fetched successfully",
                "data": {
                    "status": "success",
                    "amount": "100",
                    "currency": "ETB",
                    ...
                }
            }
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/transaction/verify/{tx_ref}",
                    headers=self.headers,
                    timeout=30.0
                )
                result = response.json()
                
                if result.get("status") != "success":
                    print(f"Chapa verification error: {result}")
                
                return result
        except Exception as e:
            print(f"Payment verification exception: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_payment_status(self, tx_ref: str) -> str:
        """
        Get payment status (success, pending, failed)
        """
        result = await self.verify_payment(tx_ref)
        
        if result.get("status") == "success":
            payment_data = result.get("data", {})
            return payment_data.get("status", "pending").lower()
        
        return "failed"


# Global payment service
payment_service = ChapaPayment()

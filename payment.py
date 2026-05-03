import httpx
import uuid
from typing import Dict, Any, Optional

class ChapaPayment:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.base_url = "https://api.chapa.co/v1"
        self.headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json"
        }
    
    async def initialize_payment(self, amount: float, email: str, 
                                first_name: str, last_name: str,
                                callback_url: str, tx_ref: str = None) -> Dict[str, Any]:
        """
        Initialize a payment with Chapa
        
        Returns:
            dict with 'status', 'message', 'data' (containing checkout_url)
        """
        if tx_ref is None:
            tx_ref = f"bingo-{uuid.uuid4()}"
        
        payload = {
            "amount": str(amount),
            "currency": "ETB",
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "tx_ref": tx_ref,
            "callback_url": callback_url,
            "return_url": callback_url,
            "customization": {
                "title": "Bingo Entry",
                "description": "Bingo game entry fee payment"
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
                
                # Log the full response for debugging
                if result.get('status') != 'success':
                    print(f"Chapa Error Response: {result}")
                
                return result
        except Exception as e:
            print(f"Payment Exception: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def verify_payment(self, tx_ref: str) -> Dict[str, Any]:
        """
        Verify a payment transaction
        
        Returns:
            dict with 'status', 'message', 'data' (containing transaction details)
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/transaction/verify/{tx_ref}",
                    headers=self.headers,
                    timeout=30.0
                )
                result = response.json()
                
                # Log the full response for debugging
                print(f"Chapa Verify Response: {result}")
                
                return result
        except Exception as e:
            print(f"Verification Exception: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def generate_tx_ref(self, user_id: int, game_id: int) -> str:
        """Generate a unique transaction reference"""
        return f"bingo-{game_id}-{user_id}-{uuid.uuid4().hex[:8]}"

import hmac
import hashlib
from urllib.parse import parse_qsl
from typing import Optional, Dict
from .config import get_settings

settings = get_settings()

def verify_telegram_web_app_data(init_data: str) -> Optional[Dict[str, str]]:
    """
    Verify Telegram Web App initData
    
    Args:
        init_data: The initData string from Telegram Web App
    
    Returns:
        Parsed data dict if valid, None if invalid
    """
    try:
        # Parse the init_data
        parsed_data = dict(parse_qsl(init_data))
        
        # Extract hash
        received_hash = parsed_data.pop("hash", None)
        if not received_hash:
            return None
        
        # Create data check string
        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
        data_check_string = "\n".join(data_check_arr)
        
        # Calculate secret key
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=settings.BOT_TOKEN.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Verify hash
        if calculated_hash != received_hash:
            return None
        
        return parsed_data
    
    except Exception as e:
        print(f"Telegram auth error: {e}")
        return None


def extract_user_from_init_data(init_data: str) -> Optional[Dict]:
    """
    Extract user information from Telegram initData
    
    Returns:
        {
            "id": 123456789,
            "first_name": "John",
            "last_name": "Doe",
            "username": "johndoe",
            "language_code": "en"
        }
    """
    verified_data = verify_telegram_web_app_data(init_data)
    if not verified_data:
        return None
    
    import json
    user_json = verified_data.get("user")
    if not user_json:
        return None
    
    try:
        user = json.loads(user_json)
        return user
    except json.JSONDecodeError:
        return None

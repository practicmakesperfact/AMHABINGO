import hmac
import hashlib
from urllib.parse import parse_qsl
from typing import Optional, Dict
from .config import get_settings

settings = get_settings()

def verify_telegram_web_app_data(init_data: str) -> Optional[Dict[str, str]]:
    """
    Verify Telegram Web App initData
    Returns parsed data dict if valid, None if invalid
    """
    try:
        parsed_data = dict(parse_qsl(init_data))
        received_hash = parsed_data.pop("hash", None)
        if not received_hash:
            return None

        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
        data_check_string = "\n".join(data_check_arr)

        # Fixed: use positional args, not keyword args
        secret_key = hmac.new(
            b"WebAppData",
            settings.BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if calculated_hash != received_hash:
            return None

        return parsed_data

    except Exception as e:
        print(f"Telegram auth error: {e}")
        return None


def extract_user_from_init_data(init_data: str) -> Optional[Dict]:
    """
    Extract user information from Telegram initData.
    Returns user dict or None.
    """
    verified_data = verify_telegram_web_app_data(init_data)
    if not verified_data:
        return None

    import json
    user_json = verified_data.get("user")
    if not user_json:
        return None

    try:
        return json.loads(user_json)
    except json.JSONDecodeError:
        return None

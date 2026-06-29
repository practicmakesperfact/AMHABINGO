import hmac
import hashlib
import json
from urllib.parse import parse_qsl
from typing import Optional, Dict
from .config import get_settings

settings = get_settings()


def verify_telegram_web_app_data(init_data: str) -> Optional[Dict[str, str]]:
    """
    Verify Telegram Web App initData using the correct HMAC-SHA256 algorithm.

    Telegram spec:
        secret_key  = HMAC-SHA256( key="WebAppData", data=<bot_token> )
        check_hash  = HMAC-SHA256( key=secret_key,   data=<data_check_string> )

    Reference: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    try:
        parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed_data.pop("hash", None)
        if not received_hash:
            return None

        # Build the data-check string: sorted key=value pairs joined by \n
        data_check_arr = sorted(f"{k}={v}" for k, v in parsed_data.items())
        data_check_string = "\n".join(data_check_arr)

        # Step 1: derive the secret key
        # key = b"WebAppData" (literal string), msg = bot_token bytes
        secret_key = hmac.new(
            b"WebAppData",                 # key  (per Telegram spec)
            settings.BOT_TOKEN.encode(),   # msg  (bot token)
            hashlib.sha256,
        ).digest()

        # Step 2: compute the expected hash
        calculated_hash = hmac.new(
            secret_key,                    # key  (derived above)
            data_check_string.encode(),    # msg  (data-check string)
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
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

    user_json = verified_data.get("user")
    if not user_json:
        return None

    try:
        return json.loads(user_json)
    except json.JSONDecodeError:
        return None

from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./bingo.db"

    # Redis (optional)
    REDIS_URL: str = "redis://localhost:6379"

    # Telegram
    BOT_TOKEN: str = "test_bot_token"
    TELEGRAM_BOT_SECRET: str = "test_secret"

    # Chapa
    CHAPA_SECRET_KEY: str = "CHASECK_TEST-test_key"
    CHAPA_WEBHOOK_SECRET: str = "test_webhook_secret"

    # App
    SECRET_KEY: str = "change-this-secret-key-in-production"
    COMMISSION_PERCENT: float = 20.0      # House takes 20% of total pot
    GAME_INTERVAL_SECONDS: int = 5        # Seconds between number calls (real Bingo pace)
    COUNTDOWN_SECONDS: int = 60           # Card selection countdown (10s for testing, 60s for production)

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

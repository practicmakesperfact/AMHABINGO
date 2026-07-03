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



    # App
    SECRET_KEY: str = "change-this-secret-key-in-production"
    COMMISSION_PERCENT: float = 20.0      # House takes 20% of total pot
    GAME_INTERVAL_SECONDS: int = 1        # Seconds between number calls (2s = fast, 5s = normal)
    COUNTDOWN_SECONDS: int = 60           # Card selection countdown (10s for testing, 60s for production)

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    
    # Admin Configuration
    ADMIN_TELEGRAM_IDS: str = "123456789"  # Comma-separated list of admin telegram_ids
    MIN_WITHDRAWAL_AMOUNT: float = 50.0    # Minimum withdrawal: 50 ETB
    MIN_DEPOSIT_AMOUNT: float = 10.0       # Minimum deposit: 10 ETB
    REFERRAL_REWARD: float = 5.0           # Referral reward: 5 ETB
    COIN_TO_ETB_RATE: int = 100            # 100 coins = 1 ETB
    
    def get_admin_ids(self) -> list[int]:
        """Parse comma-separated admin IDs."""
        return [int(x.strip()) for x in self.ADMIN_TELEGRAM_IDS.split(",") if x.strip()]

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

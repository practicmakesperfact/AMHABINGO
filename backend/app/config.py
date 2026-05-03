from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # Telegram
    BOT_TOKEN: str
    TELEGRAM_BOT_SECRET: str
    
    # Chapa
    CHAPA_SECRET_KEY: str
    CHAPA_WEBHOOK_SECRET: str
    
    # App
    SECRET_KEY: str
    COMMISSION_PERCENT: float = 10.0
    GAME_INTERVAL_SECONDS: int = 4
    
    # CORS
    FRONTEND_URL: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

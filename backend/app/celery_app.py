import os
from celery import Celery

# Create celery app
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "amhabingo_worker",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Example tasks
@celery_app.task
def verify_pending_payments():
    """Background task to verify pending payments with Chapa."""
    print("Verifying pending payments...")
    # In a real app, this would query pending transactions and call Chapa API
    pass

@celery_app.task
def cleanup_stale_games():
    """Background task to clean up old or stuck games."""
    print("Cleaning up stale games...")
    import asyncio
    
    async def _cleanup():
        from app.database import AsyncSessionLocal
        from app.models import Game, GameStatus
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as db:
            # Logic to find games stuck in WAITING/COUNTDOWN for too long
            pass
            
    # asyncio.run(_cleanup()) # Only works if properly set up with DB
    pass

# Celery Beat schedule for recurring tasks
celery_app.conf.beat_schedule = {
    'verify-payments-every-5-minutes': {
        'task': 'app.celery_app.verify_pending_payments',
        'schedule': 300.0,
    },
    'cleanup-stale-games-hourly': {
        'task': 'app.celery_app.cleanup_stale_games',
        'schedule': 3600.0,
    }
}

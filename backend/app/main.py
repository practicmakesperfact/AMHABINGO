from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy import select
import asyncio
import time

from .config import get_settings
from .database import engine, Base, AsyncSessionLocal
from .redis_client import redis_client
from .routers import user, game, payment
import json

settings = get_settings()

# Track server start time for uptime reporting
_start_time = time.time()

# Background task reference
redis_listener_task = None

async def listen_to_redis_pubsub():
    """Background task to listen to Redis Pub/Sub for game updates."""
    from .websocket import manager
    try:
        await redis_client.subscribe("game_updates")
        async for msg in redis_client.listen_messages():
            if msg and 'data' in msg:
                try:
                    payload = json.loads(msg['data'])
                    game_id = payload.get('game_id')
                    message = payload.get('message')
                    if game_id == "ALL":
                        for g_id in list(manager.active_connections.keys()):
                            await manager._local_broadcast_to_game(message, g_id)
                    elif game_id:
                        await manager._local_broadcast_to_game(message, game_id)
                except Exception as e:
                    print(f"Error parsing pubsub message: {e}")
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Redis listener crashed: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    print("Starting AMHABINGO Backend...")

    # Create / migrate tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables ready")

    # Redis (optional — game works without it via in-memory fallback)
    try:
        await redis_client.connect()
        print("Redis connected")
        
        # Start the Redis listener for Pub/Sub websocket broadcasting
        global redis_listener_task
        redis_listener_task = asyncio.create_task(listen_to_redis_pubsub())
    except Exception as e:
        print(f"Redis unavailable ({e}) - using in-memory fallback")

    # Resume game loops for any unfinished games (after crash/restart)
    try:
        from .models import Game, GameStatus
        from .game_loop import game_loop_manager
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Game).where(
                    Game.status.in_([
                        GameStatus.WAITING,
                        GameStatus.COUNTDOWN,
                        GameStatus.ACTIVE,
                    ])
                )
            )
            pending = result.scalars().all()
            for g in pending:
                print(f"Resuming loop for game {g.game_id} (status={g.status})")
                asyncio.create_task(game_loop_manager.start_countdown_loop(g.game_id))
    except Exception as e:
        print(f"Could not resume game loops: {e}")

    print("Backend ready!")
    yield

    # Shutdown
    print("Shutting down...")
    if redis_listener_task:
        redis_listener_task.cancel()
    try:
        await redis_client.disconnect()
    except Exception:
        pass
    await engine.dispose()
    print("Shutdown complete")


from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="AMHABINGO API",
    description="Real-time Bingo Game – Ethiopia",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Metrics ───────────────────────────────────────────────────────────────────
Instrumentator().instrument(app).expose(app)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Tighten to FRONTEND_URL in production if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(user.router)
app.include_router(game.router)
app.include_router(payment.router)


# ── Health & Keep-alive endpoints ─────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "ok", "message": "AMHABINGO API is running", "version": "1.0.0"}


@app.get("/ping")
async def ping():
    """
    Ultra-lightweight keep-alive endpoint.
    Used by:
      - UptimeRobot / cron-job.org to prevent Render free-plan sleep
      - Frontend polling to detect when server has woken up
    Returns in < 1ms — does NOT touch DB or Redis.
    """
    return {"pong": True, "uptime": round(time.time() - _start_time)}


@app.get("/health")
async def health_check():
    """Detailed health check for monitoring."""
    redis_ok = False
    try:
        if redis_client.redis:
            await redis_client.redis.ping()
            redis_ok = True
    except Exception:
        pass

    return {
        "status": "ok",
        "redis": "connected" if redis_ok else "disconnected (in-memory fallback active)",
        "database": "connected",
        "uptime_seconds": round(time.time() - _start_time),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import select
import asyncio

from .config import get_settings
from .database import engine, Base, AsyncSessionLocal
from .redis_client import redis_client
from .routers import user, game, payment

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    print("Starting AMHABINGO Backend...")

    # Create / migrate tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables ready")

    # Redis (optional – game works without it)
    try:
        await redis_client.connect()
        print("Redis connected")
    except Exception as e:
        print(f"Redis unavailable ({e}) - using in-memory fallback")

    # Resume game loops for any unfinished games
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
    try:
        await redis_client.disconnect()
    except Exception:
        pass
    await engine.dispose()
    print("Shutdown complete")


app = FastAPI(
    title="AMHABINGO API",
    description="Real-time Bingo Game – Ethiopia",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(user.router)
app.include_router(game.router)
app.include_router(payment.router)


# ── Health endpoints ──────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"status": "ok", "message": "AMHABINGO API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    redis_ok = False
    try:
        if redis_client.redis:
            await redis_client.redis.ping()
            redis_ok = True
    except Exception:
        pass
    return {
        "status": "ok",
        "redis": "connected" if redis_ok else "disconnected",
        "database": "connected",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

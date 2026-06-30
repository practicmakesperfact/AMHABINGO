from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .config import get_settings

settings = get_settings()

# Determine if we're using SQLite (local dev) or PostgreSQL (production)
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Build connect_args based on database type
if _is_sqlite:
    _connect_args = {"check_same_thread": False}
    _pool_kwargs = {}  # SQLite doesn't support pool_size/max_overflow with StaticPool
else:
    # asyncpg-specific connection arguments for PostgreSQL
    _connect_args = {
        "command_timeout": 60,          # Max seconds for a single query
        "server_settings": {
            "application_name": "amhabingo_backend",
            "jit": "off",               # Disable JIT for more predictable latency
        },
    }
    _pool_kwargs = {
        "pool_size": 20,                # Maintain 20 persistent connections (handles 600 users)
        "max_overflow": 30,             # Allow 30 extra connections under burst load
        "pool_timeout": 30,             # Wait up to 30s for a connection from the pool
        "pool_recycle": 1800,           # Recycle connections every 30 minutes (Neon drops idle ones)
        "pool_pre_ping": True,          # Test connection health before using (prevents stale conn errors)
    }

# Create async engine
# echo=False — CRITICAL: never log SQL in production, it floods Render logs
# and adds latency under load
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=_connect_args,
    **_pool_kwargs,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


# Dependency for FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Initialize database tables
async def init_db():
    """Create all database tables with retry logic."""
    import asyncio
    from . import models  # noqa: F401 — registers models with Base

    max_retries = 3
    retry_delay = 5  # seconds

    for attempt in range(max_retries):
        try:
            print(f"Initialising database (attempt {attempt + 1}/{max_retries})...")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("Database tables ready!")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"DB init failed: {str(e)[:120]}")
                print(f"Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
            else:
                print(f"DB init failed after {max_retries} attempts")
                raise

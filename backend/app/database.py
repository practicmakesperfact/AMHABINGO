from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .config import get_settings

settings = get_settings()

# Create async engine with connection pooling and timeout settings
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True,
    pool_size=10,                    # Number of connections to maintain
    max_overflow=20,                 # Allow up to 20 additional connections
    pool_timeout=30,                 # Wait 30s for connection from pool
    pool_recycle=3600,              # Recycle connections after 1 hour
    pool_pre_ping=True,             # Test connections before using
    connect_args={
        "timeout": 30,              # Connection timeout in seconds
        "command_timeout": 60,      # Command execution timeout
        "server_settings": {
            "application_name": "amhabingo_backend",
            "jit": "off"            # Disable JIT for faster queries
        }
    }
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
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
    """Create all database tables with retry logic"""
    import asyncio
    from . import models  # Import models to register them with Base
    
    max_retries = 3
    retry_delay = 5  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"🔧 Attempting to initialize database (attempt {attempt + 1}/{max_retries})...")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ Database tables created successfully!")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️ Failed: {str(e)[:100]}")
                print(f"⏳ Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print(f"❌ Failed after {max_retries} attempts")
                raise

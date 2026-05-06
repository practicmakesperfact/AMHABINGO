from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .config import get_settings
from .database import engine, Base
from .redis_client import redis_client
from .routers import user, game, payment

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting AMHABINGO Backend...")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Connect to Redis (optional)
    try:
        await redis_client.connect()
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠️  Redis connection failed: {e}")
        print("⚠️  Continuing without Redis (some features may be limited)")
    
    print("✅ Backend started successfully!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    try:
        await redis_client.disconnect()
    except:
        pass
    await engine.dispose()
    print("✅ Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="AMHABINGO API",
    description="Real-time Bingo Game API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "https://web.telegram.org"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(user.router)
app.include_router(game.router)
app.include_router(payment.router)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "AMHABINGO API is running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    # Check Redis
    redis_ok = False
    try:
        if redis_client.redis:
            await redis_client.redis.ping()
            redis_ok = True
    except Exception as e:
        print(f"⚠️  Redis health check failed: {e}")
    
    return {
        "status": "ok",
        "redis": "connected" if redis_ok else "disconnected",
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

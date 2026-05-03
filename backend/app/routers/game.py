from fastapi import APIRouter, Depends, HTTPException, Header, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from ..database import get_db
from ..models import Game, Player, User, GameStatus
from ..schemas import GameResponse, PlayerResponse, GameCreate, PlayerCreate
from ..auth import extract_user_from_init_data
from ..game_engine import GameManager
from ..websocket import manager, handle_websocket_message
from ..redis_client import redis_client
import asyncio

router = APIRouter(prefix="/api/games", tags=["games"])

@router.post("/", response_model=GameResponse)
async def create_game(
    game_data: GameCreate,
    init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    """Create a new game"""
    user_data = extract_user_from_init_data(init_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    game_manager = GameManager(db)
    game = await game_manager.create_game(game_data.room, game_data.entry_fee)
    
    return game

@router.get("/", response_model=List[GameResponse])
async def list_games(
    status: str = None,
    room: str = None,
    db: AsyncSession = Depends(get_db)
):
    """List games with optional filters"""
    query = select(Game)
    
    if status:
        query = query.where(Game.status == status)
    if room:
        query = query.where(Game.room == room)
    
    query = query.order_by(Game.created_at.desc()).limit(50)
    
    result = await db.execute(query)
    games = result.scalars().all()
    
    return games

@router.get("/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get game by ID"""
    result = await db.execute(
        select(Game).where(Game.game_id == game_id)
    )
    game = result.scalar_one_or_none()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return game

@router.get("/{game_id}/players", response_model=List[PlayerResponse])
async def get_game_players(
    game_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all players in a game"""
    # Get game
    game_result = await db.execute(
        select(Game).where(Game.game_id == game_id)
    )
    game = game_result.scalar_one_or_none()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Get players
    players_result = await db.execute(
        select(Player).where(Player.game_id == game.id)
    )
    players = players_result.scalars().all()
    
    return players

@router.get("/{game_id}/available-cards")
async def get_available_cards(
    game_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get list of available cards (1-600)"""
    # Check if game exists
    result = await db.execute(
        select(Game).where(Game.game_id == game_id)
    )
    game = result.scalar_one_or_none()
    
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Get taken cards from Redis
    taken_cards = await redis_client.get_all_taken_cards(game_id)
    
    # Generate available cards list
    all_cards = set(range(1, 601))
    taken_card_numbers = set(taken_cards.keys())
    available_cards = list(all_cards - taken_card_numbers)
    
    return {
        "available_cards": available_cards,
        "taken_cards": taken_cards,
        "total_available": len(available_cards),
        "total_taken": len(taken_cards)
    }

@router.post("/{game_id}/join", response_model=PlayerResponse)
async def join_game(
    game_id: str,
    player_data: PlayerCreate,
    init_data: str = Header(..., alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    """Join a game (requires payment verification)"""
    user_data = extract_user_from_init_data(init_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram data")
    
    telegram_id = user_data.get("id")
    
    # Get user
    user_result = await db.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Join game
    game_manager = GameManager(db)
    try:
        player = await game_manager.join_game(game_id, user.id, player_data.card_number)
        return player
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.websocket("/ws/{game_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    game_id: str,
    user_id: int
):
    """WebSocket endpoint for real-time game updates"""
    await manager.connect(websocket, game_id, user_id)
    
    try:
        # Send initial state
        taken_cards = await redis_client.get_all_taken_cards(game_id)
        await manager.send_personal_message({
            "type": "initial_state",
            "data": {
                "taken_cards": taken_cards
            }
        }, websocket)
        
        # Listen for messages
        while True:
            data = await websocket.receive_json()
            await handle_websocket_message(data, websocket, game_id)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, game_id)

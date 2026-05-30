from fastapi import APIRouter, Depends, HTTPException, Header, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from ..database import get_db
from ..models import Game, Player, User, GameStatus, Transaction
from ..schemas import GameResponse, PlayerResponse, GameCreate, PlayerCreate, UserResponse
from ..auth import extract_user_from_init_data
from ..game_engine import GameManager
from ..websocket import manager, handle_websocket_message
from ..redis_client import redis_client
import asyncio

router = APIRouter(prefix="/api/games", tags=["games"])


# ─── Lazy-import to avoid circular imports ───────────────────────────────────
def _get_game_loop_manager():
    from ..game_loop import game_loop_manager
    return game_loop_manager


# ─── Create Game ─────────────────────────────────────────────────────────────
@router.post("/", response_model=GameResponse)
async def create_game(
    game_data: GameCreate,
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    """Create a new game and immediately start 60s countdown."""
    if init_data:
        user_data = extract_user_from_init_data(init_data)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid Telegram data")

    game_manager = GameManager(db)
    game = await game_manager.create_game(game_data.room, game_data.entry_fee)

    # Auto-start countdown loop
    loop_mgr = _get_game_loop_manager()
    asyncio.create_task(loop_mgr.start_countdown_loop(game.game_id))

    return game


# ─── List Games ──────────────────────────────────────────────────────────────
@router.get("/", response_model=List[GameResponse])
async def list_games(
    status: Optional[str] = None,
    room: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List games with optional filters."""
    query = select(Game)
    if status:
        query = query.where(Game.status == status)
    if room:
        query = query.where(Game.room == room)
    query = query.order_by(Game.created_at.desc()).limit(50)

    result = await db.execute(query)
    return result.scalars().all()


# ─── Active Games ─────────────────────────────────────────────────────────────
@router.get("/active", response_model=List[GameResponse])
async def get_active_games(db: AsyncSession = Depends(get_db)):
    """Return all waiting or active games."""
    result = await db.execute(
        select(Game)
        .where(Game.status.in_([GameStatus.WAITING, GameStatus.COUNTDOWN, GameStatus.ACTIVE]))
        .order_by(Game.created_at.desc())
        .limit(20)
    )
    return result.scalars().all()


# ─── Get Single Game ──────────────────────────────────────────────────────────
@router.get("/{game_id}", response_model=GameResponse)
async def get_game(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.game_id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


# ─── Players in Game ──────────────────────────────────────────────────────────
@router.get("/{game_id}/players", response_model=List[PlayerResponse])
async def get_game_players(game_id: str, db: AsyncSession = Depends(get_db)):
    game_result = await db.execute(select(Game).where(Game.game_id == game_id))
    game = game_result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    players_result = await db.execute(select(Player).where(Player.game_id == game.id))
    return players_result.scalars().all()


# ─── Available Cards ──────────────────────────────────────────────────────────
@router.get("/{game_id}/available-cards")
async def get_available_cards(game_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Game).where(Game.game_id == game_id))
    game = result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    taken_cards: dict = {}
    try:
        taken_cards = await redis_client.get_all_taken_cards(game_id)
    except Exception:
        pass

    all_cards = set(range(1, 601))
    available = sorted(list(all_cards - set(taken_cards.keys())))

    return {
        "available_cards": available,
        "taken_cards": taken_cards,
        "total_available": len(available),
        "total_taken": len(taken_cards)
    }


# ─── Get Player Card ──────────────────────────────────────────────────────────
@router.get("/{game_id}/player/{user_id}/card")
async def get_player_card(game_id: str, user_id: int, db: AsyncSession = Depends(get_db)):
    game_result = await db.execute(select(Game).where(Game.game_id == game_id))
    game = game_result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    player_result = await db.execute(
        select(Player).where(Player.game_id == game.id, Player.user_id == user_id)
    )
    player = player_result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found in this game")

    return {
        "card_number": player.card_number,
        "card_data": player.card_data,
        "marked_numbers": player.marked_numbers,
        "has_won": player.has_won,
    }


# ─── Join Game ────────────────────────────────────────────────────────────────
@router.post("/{game_id}/join", response_model=PlayerResponse)
async def join_game(
    game_id: str,
    player_data: PlayerCreate,
    init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    db: AsyncSession = Depends(get_db)
):
    """Join a game. Deducts entry fee from balance."""
    # Resolve user
    if not init_data:
        user_result = await db.execute(select(User).where(User.telegram_id == 123456789))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Demo user not found. Authenticate first.")
    else:
        user_data = extract_user_from_init_data(init_data)
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid Telegram data")
        user_result = await db.execute(select(User).where(User.telegram_id == user_data["id"]))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    # Get game
    game_result = await db.execute(select(Game).where(Game.game_id == game_id))
    game = game_result.scalar_one_or_none()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    if game.status not in [GameStatus.WAITING, GameStatus.COUNTDOWN, GameStatus.ACTIVE]:
        raise HTTPException(status_code=400, detail="Game has already finished")

    # Check balance
    total_balance = user.balance + user.play_balance
    if total_balance < game.entry_fee:
        raise HTTPException(status_code=400, detail=f"Insufficient balance. Need {game.entry_fee} ETB")

    game_manager = GameManager(db)
    try:
        player = await game_manager.join_game(game_id, user.id, player_data.card_number)
        
        # Deduct fee: from play_balance first, then balance
        remaining_fee = game.entry_fee
        if user.play_balance >= remaining_fee:
            user.play_balance -= remaining_fee
        else:
            remaining_fee -= user.play_balance
            user.play_balance = 0.0
            user.balance -= remaining_fee
            
        user.games_played += 1
        await db.commit()
        return player
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── WebSocket Endpoint ───────────────────────────────────────────────────────
@router.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, user_id: int = 0):
    """Real-time WebSocket for game updates."""
    await manager.connect(websocket, game_id, user_id)

    try:
        # Send initial card state
        taken_cards: dict = {}
        try:
            taken_cards = await redis_client.get_all_taken_cards(game_id)
        except Exception:
            pass

        # Also get current game state
        game_state = None
        try:
            game_state = await redis_client.get_game_state(game_id)
        except Exception:
            pass

        await manager.send_personal_message({
            "type": "initial_state",
            "data": {
                "taken_cards": taken_cards,
                "game_state": game_state
            }
        }, websocket)

        while True:
            data = await websocket.receive_json()
            await handle_websocket_message(data, websocket, game_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, game_id)

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set
import json
import asyncio
from .redis_client import redis_client


class ConnectionManager:
    """Manages WebSocket connections for all active games."""

    def __init__(self):
        # game_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> user_id mapping
        self.connection_users: Dict[WebSocket, int] = {}

    async def connect(self, websocket: WebSocket, game_id: str, user_id: int):
        """Accept and register a new connection."""
        await websocket.accept()

        if game_id not in self.active_connections:
            self.active_connections[game_id] = set()

        self.active_connections[game_id].add(websocket)
        self.connection_users[websocket] = user_id

    def disconnect(self, websocket: WebSocket, game_id: str):
        """Remove a connection and clean up empty rooms."""
        if game_id in self.active_connections:
            self.active_connections[game_id].discard(websocket)
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]

        self.connection_users.pop(websocket, None)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")

    async def broadcast_to_game(self, message: dict, game_id: str):
        """Broadcast a message to every connection in a game room."""
        if game_id not in self.active_connections:
            return

        disconnected = []
        # Snapshot the set so we can modify it while iterating
        connections = list(self.active_connections.get(game_id, set()))
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection, game_id)

    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all active connections across all games."""
        for game_id in list(self.active_connections.keys()):
            await self.broadcast_to_game(message, game_id)

    def get_game_connections_count(self, game_id: str) -> int:
        return len(self.active_connections.get(game_id, set()))

    def get_user_id(self, websocket: WebSocket) -> int:
        return self.connection_users.get(websocket, 0)


# Global connection manager singleton
manager = ConnectionManager()


# ── WebSocket message handlers ────────────────────────────────────────────────

async def handle_select_card(data: dict, websocket: WebSocket, game_id: str):
    """Handle card selection from a client."""
    card_number = data.get("card_number")
    user_id = manager.get_user_id(websocket)

    if not card_number or not user_id:
        await manager.send_personal_message(
            {"type": "error", "message": "Invalid card selection"}, websocket
        )
        return

    # Check if card is already taken by someone else
    taken_by = await redis_client.get_card_status(game_id, card_number)

    if taken_by and taken_by != user_id:
        await manager.send_personal_message(
            {"type": "error", "message": f"Card {card_number} is already taken"}, websocket
        )
        return

    # Mark card as taken in Redis
    await redis_client.set_card_status(game_id, card_number, user_id)

    # Broadcast to all players in the room
    await manager.broadcast_to_game(
        {"type": "card_selected", "data": {"card_number": card_number, "user_id": user_id}},
        game_id,
    )


async def handle_unselect_card(data: dict, websocket: WebSocket, game_id: str):
    """Handle card unselection. Uses the safe abstraction layer (never crashes)."""
    card_number = data.get("card_number")
    user_id = manager.get_user_id(websocket)

    if not card_number or not user_id:
        return

    # Only the owner may unselect
    taken_by = await redis_client.get_card_status(game_id, card_number)
    if taken_by != user_id:
        return

    # Remove via safe abstraction — works whether Redis is available or not
    key = f"game:{game_id}:cards"
    if redis_client._available and redis_client.redis:
        try:
            await redis_client.redis.hdel(key, str(card_number))
        except Exception as e:
            print(f"Redis hdel failed, using in-memory fallback: {e}")
            # Fallback: remove from in-memory dict
            from .redis_client import _hashes
            _hashes.get(key, {}).pop(str(card_number), None)
    else:
        # In-memory fallback
        from .redis_client import _hashes
        _hashes.get(key, {}).pop(str(card_number), None)

    # Broadcast availability to all players
    await manager.broadcast_to_game(
        {"type": "card_available", "data": {"card_number": card_number}},
        game_id,
    )


async def handle_claim_win(data: dict, websocket: WebSocket, game_id: str):
    """Handle win claim — actual validation happens server-side in game_loop."""
    user_id = manager.get_user_id(websocket)
    await manager.send_personal_message(
        {"type": "win_claim_received", "data": {"user_id": user_id}}, websocket
    )


# ── Message router ────────────────────────────────────────────────────────────

async def handle_websocket_message(message: dict, websocket: WebSocket, game_id: str):
    """Route incoming WebSocket messages to the appropriate handler."""
    msg_type = message.get("type")
    data = message.get("data", {})

    handlers = {
        "select_card":   handle_select_card,
        "unselect_card": handle_unselect_card,
        "claim_win":     handle_claim_win,
    }

    handler = handlers.get(msg_type)
    if handler:
        await handler(data, websocket, game_id)
    else:
        await manager.send_personal_message(
            {"type": "error", "message": f"Unknown message type: {msg_type}"}, websocket
        )


# ── Broadcast helpers (called from game_loop) ─────────────────────────────────

async def broadcast_timer_update(game_id: str, seconds: int):
    await manager.broadcast_to_game(
        {"type": "timer_update", "data": {"seconds": seconds}}, game_id
    )


async def broadcast_game_started(game_id: str):
    await manager.broadcast_to_game(
        {"type": "game_started", "data": {"game_id": game_id}}, game_id
    )


async def broadcast_number_called(game_id: str, number: int, category: str):
    await manager.broadcast_to_game(
        {"type": "number_called", "data": {"number": number, "category": category}}, game_id
    )


async def broadcast_player_won(game_id: str, winners: List[dict]):
    await manager.broadcast_to_game(
        {"type": "player_won", "data": {"winners": winners}}, game_id
    )


async def broadcast_game_state(game_id: str, total_players: int, prize_pool: float):
    await manager.broadcast_to_game(
        {"type": "game_state_update", "data": {"total_players": total_players, "prize_pool": prize_pool}},
        game_id,
    )

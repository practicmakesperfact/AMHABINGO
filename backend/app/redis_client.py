"""
Redis client with full in-memory fallback.
If Redis is unavailable the game still works perfectly using in-memory dicts.
"""

import json
import asyncio
from typing import Optional, List, Dict, Any
from .config import get_settings

settings = get_settings()

# ── In-memory fallback storage ────────────────────────────────────────────────
_mem: Dict[str, Any] = {}          # generic key-value
_hashes: Dict[str, Dict] = {}      # hash maps  (game:X:cards)
_lists: Dict[str, List] = {}       # lists       (game:X:called)
_sets: Dict[str, set] = {}         # sets        (active_games)


class RedisClient:
    def __init__(self):
        self.redis = None
        self.pubsub = None
        self._available = False

    # ── Connection ────────────────────────────────────────────────────────────
    async def connect(self):
        try:
            import redis.asyncio as aioredis
            self.redis = await aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
            )
            await self.redis.ping()
            self.pubsub = self.redis.pubsub()
            self._available = True
            print("✅ Redis connected")
        except Exception as e:
            self._available = False
            self.redis = None
            raise e

    async def disconnect(self):
        if self.pubsub:
            try:
                await self.pubsub.close()
            except Exception:
                pass
        if self.redis:
            try:
                await self.redis.close()
            except Exception:
                pass

    # ── Game State ────────────────────────────────────────────────────────────
    async def set_game_state(self, game_id: str, state: Dict[str, Any], ttl: int = 7200):
        key = f"game:{game_id}"
        if self._available:
            try:
                await self.redis.setex(key, ttl, json.dumps(state))
                return
            except Exception:
                pass
        _mem[key] = state

    async def get_game_state(self, game_id: str) -> Optional[Dict[str, Any]]:
        key = f"game:{game_id}"
        if self._available:
            try:
                data = await self.redis.get(key)
                return json.loads(data) if data else None
            except Exception:
                pass
        return _mem.get(key)

    async def delete_game_state(self, game_id: str):
        key = f"game:{game_id}"
        if self._available:
            try:
                await self.redis.delete(key)
                return
            except Exception:
                pass
        _mem.pop(key, None)

    # ── Card Availability ─────────────────────────────────────────────────────
    async def set_card_status(self, game_id: str, card_number: int, user_id: int):
        key = f"game:{game_id}:cards"
        if self._available:
            try:
                await self.redis.hset(key, str(card_number), str(user_id))
                return
            except Exception:
                pass
        _hashes.setdefault(key, {})[str(card_number)] = str(user_id)

    async def get_card_status(self, game_id: str, card_number: int) -> Optional[int]:
        key = f"game:{game_id}:cards"
        if self._available:
            try:
                val = await self.redis.hget(key, str(card_number))
                return int(val) if val else None
            except Exception:
                pass
        val = _hashes.get(key, {}).get(str(card_number))
        return int(val) if val else None

    async def get_all_taken_cards(self, game_id: str) -> Dict[int, int]:
        key = f"game:{game_id}:cards"
        if self._available:
            try:
                cards = await self.redis.hgetall(key)
                return {int(k): int(v) for k, v in cards.items()}
            except Exception:
                pass
        raw = _hashes.get(key, {})
        return {int(k): int(v) for k, v in raw.items()}

    async def clear_game_cards(self, game_id: str):
        key = f"game:{game_id}:cards"
        if self._available:
            try:
                await self.redis.delete(key)
                return
            except Exception:
                pass
        _hashes.pop(key, None)

    # ── Timer ─────────────────────────────────────────────────────────────────
    async def set_timer(self, game_id: str, seconds: int):
        key = f"game:{game_id}:timer"
        if self._available:
            try:
                await self.redis.setex(key, seconds + 30, str(seconds))
                return
            except Exception:
                pass
        _mem[key] = seconds

    async def get_timer(self, game_id: str) -> Optional[int]:
        key = f"game:{game_id}:timer"
        if self._available:
            try:
                val = await self.redis.get(key)
                return int(val) if val else None
            except Exception:
                pass
        val = _mem.get(key)
        return int(val) if val is not None else None

    async def decrement_timer(self, game_id: str) -> int:
        key = f"game:{game_id}:timer"
        if self._available:
            try:
                return await self.redis.decr(key)
            except Exception:
                pass
        cur = int(_mem.get(key, 0)) - 1
        _mem[key] = cur
        return cur

    # ── Called Numbers ────────────────────────────────────────────────────────
    async def add_called_number(self, game_id: str, number: int):
        key = f"game:{game_id}:called"
        if self._available:
            try:
                await self.redis.rpush(key, str(number))
                return
            except Exception:
                pass
        _lists.setdefault(key, []).append(str(number))

    async def get_called_numbers(self, game_id: str) -> List[int]:
        key = f"game:{game_id}:called"
        if self._available:
            try:
                nums = await self.redis.lrange(key, 0, -1)
                return [int(n) for n in nums]
            except Exception:
                pass
        return [int(n) for n in _lists.get(key, [])]

    async def clear_called_numbers(self, game_id: str):
        key = f"game:{game_id}:called"
        if self._available:
            try:
                await self.redis.delete(key)
                return
            except Exception:
                pass
        _lists.pop(key, None)

    # ── Active Games ──────────────────────────────────────────────────────────
    async def add_active_game(self, game_id: str):
        if self._available:
            try:
                await self.redis.sadd("active_games", game_id)
                return
            except Exception:
                pass
        _sets.setdefault("active_games", set()).add(game_id)

    async def remove_active_game(self, game_id: str):
        if self._available:
            try:
                await self.redis.srem("active_games", game_id)
                return
            except Exception:
                pass
        _sets.get("active_games", set()).discard(game_id)

    async def get_active_games(self) -> List[str]:
        if self._available:
            try:
                games = await self.redis.smembers("active_games")
                return list(games)
            except Exception:
                pass
        return list(_sets.get("active_games", set()))

    # ── Pub/Sub (best-effort) ─────────────────────────────────────────────────
    async def publish(self, channel: str, message: Dict[str, Any]):
        if self._available:
            try:
                await self.redis.publish(channel, json.dumps(message))
            except Exception:
                pass

    async def subscribe(self, *channels: str):
        if self._available and self.pubsub:
            try:
                await self.pubsub.subscribe(*channels)
            except Exception:
                pass

    async def get_message(self):
        if self._available and self.pubsub:
            try:
                return await self.pubsub.get_message(ignore_subscribe_messages=True)
            except Exception:
                pass
        return None

    # ── User Session ──────────────────────────────────────────────────────────
    async def set_user_session(self, user_id: int, data: Dict[str, Any], ttl: int = 86400):
        key = f"session:{user_id}"
        if self._available:
            try:
                await self.redis.setex(key, ttl, json.dumps(data))
                return
            except Exception:
                pass
        _mem[key] = data

    async def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        key = f"session:{user_id}"
        if self._available:
            try:
                data = await self.redis.get(key)
                return json.loads(data) if data else None
            except Exception:
                pass
        return _mem.get(key)


# Singleton
redis_client = RedisClient()

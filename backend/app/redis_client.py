import redis.asyncio as redis
import json
from typing import Optional, List, Dict, Any
from .config import get_settings

settings = get_settings()

class RedisClient:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
    
    async def connect(self):
        """Connect to Redis"""
        self.redis = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        self.pubsub = self.redis.pubsub()
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
    
    # Game State Management
    async def set_game_state(self, game_id: str, state: Dict[str, Any], ttl: int = 3600):
        """Store game state"""
        key = f"game:{game_id}"
        await self.redis.setex(key, ttl, json.dumps(state))
    
    async def get_game_state(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get game state"""
        key = f"game:{game_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def delete_game_state(self, game_id: str):
        """Delete game state"""
        key = f"game:{game_id}"
        await self.redis.delete(key)
    
    # Card Availability (1-600)
    async def set_card_status(self, game_id: str, card_number: int, user_id: int):
        """Mark card as taken"""
        key = f"game:{game_id}:cards"
        await self.redis.hset(key, str(card_number), str(user_id))
    
    async def get_card_status(self, game_id: str, card_number: int) -> Optional[int]:
        """Check if card is taken"""
        key = f"game:{game_id}:cards"
        user_id = await self.redis.hget(key, str(card_number))
        return int(user_id) if user_id else None
    
    async def get_all_taken_cards(self, game_id: str) -> Dict[int, int]:
        """Get all taken cards"""
        if not self.redis:
            return {}
        
        try:
            key = f"game:{game_id}:cards"
            cards = await self.redis.hgetall(key)
            return {int(k): int(v) for k, v in cards.items()}
        except Exception as e:
            print(f"⚠️  Redis error in get_all_taken_cards: {e}")
            return {}
    
    async def clear_game_cards(self, game_id: str):
        """Clear all card selections"""
        key = f"game:{game_id}:cards"
        await self.redis.delete(key)
    
    # Timer Management
    async def set_timer(self, game_id: str, seconds: int):
        """Set countdown timer"""
        key = f"game:{game_id}:timer"
        await self.redis.setex(key, seconds + 10, str(seconds))
    
    async def get_timer(self, game_id: str) -> Optional[int]:
        """Get remaining time"""
        key = f"game:{game_id}:timer"
        seconds = await self.redis.get(key)
        return int(seconds) if seconds else None
    
    async def decrement_timer(self, game_id: str) -> int:
        """Decrement timer by 1"""
        key = f"game:{game_id}:timer"
        return await self.redis.decr(key)
    
    # Called Numbers
    async def add_called_number(self, game_id: str, number: int):
        """Add called number to list"""
        key = f"game:{game_id}:called"
        await self.redis.rpush(key, str(number))
    
    async def get_called_numbers(self, game_id: str) -> List[int]:
        """Get all called numbers"""
        key = f"game:{game_id}:called"
        numbers = await self.redis.lrange(key, 0, -1)
        return [int(n) for n in numbers]
    
    async def clear_called_numbers(self, game_id: str):
        """Clear called numbers"""
        key = f"game:{game_id}:called"
        await self.redis.delete(key)
    
    # Pub/Sub for Broadcasting
    async def publish(self, channel: str, message: Dict[str, Any]):
        """Publish message to channel"""
        await self.redis.publish(channel, json.dumps(message))
    
    async def subscribe(self, *channels: str):
        """Subscribe to channels"""
        await self.pubsub.subscribe(*channels)
    
    async def unsubscribe(self, *channels: str):
        """Unsubscribe from channels"""
        await self.pubsub.unsubscribe(*channels)
    
    async def get_message(self):
        """Get next message from subscribed channels"""
        return await self.pubsub.get_message(ignore_subscribe_messages=True)
    
    # Active Games List
    async def add_active_game(self, game_id: str):
        """Add game to active games set"""
        await self.redis.sadd("active_games", game_id)
    
    async def remove_active_game(self, game_id: str):
        """Remove game from active games set"""
        await self.redis.srem("active_games", game_id)
    
    async def get_active_games(self) -> List[str]:
        """Get all active game IDs"""
        games = await self.redis.smembers("active_games")
        return list(games)
    
    # User Session
    async def set_user_session(self, user_id: int, session_data: Dict[str, Any], ttl: int = 86400):
        """Store user session"""
        key = f"session:{user_id}"
        await self.redis.setex(key, ttl, json.dumps(session_data))
    
    async def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user session"""
        key = f"session:{user_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None

# Global Redis client instance
redis_client = RedisClient()

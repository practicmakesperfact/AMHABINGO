"""
Game loop manager.
Handles: countdown → active → finish → auto-create next game.
Works with or without Redis.
"""

import asyncio
from datetime import datetime
from sqlalchemy import select

from .models import Game, Player, User, GameStatus
from .database import AsyncSessionLocal
from .game_engine import GameManager, BingoGameEngine
from .websocket import (
    broadcast_timer_update,
    broadcast_game_started,
    broadcast_number_called,
    broadcast_player_won,
    manager as ws_manager,
)
from .redis_client import redis_client
from .config import get_settings

settings = get_settings()


class GameLoopManager:
    """One asyncio Task per active game."""

    def __init__(self):
        self.active_loops: dict[str, asyncio.Task] = {}

    # ── Public API ────────────────────────────────────────────────────────────
    async def start_countdown_loop(self, game_id: str):
        if game_id in self.active_loops:
            return
        task = asyncio.create_task(self._run(game_id))
        self.active_loops[game_id] = task

    def stop_game_loop(self, game_id: str):
        task = self.active_loops.pop(game_id, None)
        if task:
            task.cancel()

    # ── Internal ──────────────────────────────────────────────────────────────
    async def _run(self, game_id: str):
        try:
            await self._countdown(game_id)
            await self._game_loop(game_id)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"❌ Game loop error [{game_id}]: {e}")
        finally:
            self.active_loops.pop(game_id, None)

    # ── Card-selection countdown ──────────────────────────────────────────────
    async def _countdown(self, game_id: str):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Game).where(Game.game_id == game_id))
            game = result.scalar_one_or_none()
            if not game:
                return

            # If already active or finished, skip countdown
            if game.status in (GameStatus.ACTIVE, GameStatus.FINISHED):
                return

            seconds = game.countdown_seconds or settings.COUNTDOWN_SECONDS
            game.status = GameStatus.COUNTDOWN
            await db.commit()

        try:
            await redis_client.set_timer(game_id, seconds)
        except Exception:
            pass

        for remaining in range(seconds, -1, -1):
            try:
                await redis_client.set_timer(game_id, remaining)
            except Exception:
                pass
            await broadcast_timer_update(game_id, remaining)
            await asyncio.sleep(1)

    # ── Main game loop ────────────────────────────────────────────────────────
    async def _game_loop(self, game_id: str):
        # Small delay after countdown to allow last-second joins
        await asyncio.sleep(2)
        
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Game).where(Game.game_id == game_id))
            game = result.scalar_one_or_none()
            if not game:
                return

            # Check if game has players
            if game.total_players == 0:
                # No players, finish immediately and create next game
                game.status = GameStatus.FINISHED
                await db.commit()
                print(f"⚠️ Game {game_id} has no players, finishing immediately")
                await asyncio.sleep(3)
                await self._create_next_game(game_id)
                return

            # Mark ACTIVE
            game.status = GameStatus.ACTIVE
            game.started_at = datetime.utcnow()
            await db.commit()
            await broadcast_game_started(game_id)

            game_manager = GameManager(db)

            while True:
                # Refresh
                await db.refresh(game)
                if game.status != GameStatus.ACTIVE:
                    break

                # Call next number
                number = await game_manager.call_number(game_id)
                if number is None:
                    # All 75 called, no winner
                    await game_manager.finish_game(game_id, [])
                    await broadcast_player_won(game_id, [])
                    break

                letter = BingoGameEngine.get_number_category(number)
                await broadcast_number_called(game_id, number, letter)

                await asyncio.sleep(1)   # brief pause before win check

                winners = await game_manager.check_winners(game_id)
                if winners:
                    winner_ids = [w.user_id for w in winners]
                    prize = await game_manager.finish_game(game_id, winner_ids)

                    winner_data = []
                    for w in winners:
                        u_res = await db.execute(select(User).where(User.id == w.user_id))
                        u = u_res.scalar_one_or_none()
                        winner_data.append({
                            "user_id": w.user_id,
                            "username": (u.username or u.first_name) if u else f"Player{w.user_id}",
                            "card_number": w.card_number,
                            "card_data": w.card_data,
                            "winning_pattern": w.winning_pattern,
                            "prize_amount": prize or 0,
                        })

                    await broadcast_player_won(game_id, winner_data)
                    break

                await asyncio.sleep(settings.GAME_INTERVAL_SECONDS)

        # Auto-create next game after short delay
        await asyncio.sleep(6)
        await self._create_next_game(game_id)

    # ── Auto-create next game ─────────────────────────────────────────────────
    async def _create_next_game(self, old_game_id: str):
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Game).where(Game.game_id == old_game_id))
                old = result.scalar_one_or_none()
                if not old:
                    return

                # Don't create next game if old game had no players
                if old.total_players == 0:
                    print(f"⚠️ Not creating next game after {old_game_id} (no players)")
                    return

                gm = GameManager(db)
                new_game = await gm.create_game(old.room, old.entry_fee)
                print(f"✅ Next game created: {new_game.game_id} (stake={old.entry_fee})")

                # Tell all connected clients
                await ws_manager.broadcast_to_game({
                    "type": "next_game",
                    "data": {"game_id": new_game.game_id, "entry_fee": old.entry_fee},
                }, old_game_id)

                # Start its countdown
                await self.start_countdown_loop(new_game.game_id)

        except Exception as e:
            print(f"❌ Failed to create next game after {old_game_id}: {e}")


# Singleton
game_loop_manager = GameLoopManager()

"""
Game loop manager.
Handles: countdown → active → finish → auto-create next game.

Performance-critical changes vs original:
- mark_number_on_all_cards() is NO LONGER called every second.
  Numbers are only tracked in Redis (called_numbers list).
  The frontend marks numbers locally by comparing the card to called numbers.
  DB player records are only updated once, at game end (winners).
- This eliminates 600 DB writes per second under full load.
"""

import asyncio
from datetime import datetime
from sqlalchemy import select

from .models import Game, Player, User, GameStatus
from .database import AsyncSessionLocal
from .game_engine import GameManager, BingoGameEngine
from .websocket import (
    broadcast_timer_update,
    broadcast_countdown_started,
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
            print(f"Game loop error [{game_id}]: {e}")
            import traceback
            traceback.print_exc()
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

            # Update Redis state
            try:
                await redis_client.set_game_state(game_id, {
                    "status": GameStatus.COUNTDOWN.value,
                    "players": game.total_players,
                    "called_numbers": [],
                    "current_number": None
                })
            except Exception:
                pass

        import time
        starts_at = time.time() + seconds

        try:
            await redis_client.set_timer(game_id, seconds)
        except Exception:
            pass

        # Broadcast the start time once so late-joining clients can sync
        await broadcast_countdown_started(game_id, seconds, starts_at)

        # Tick every second so the frontend timer counts down correctly
        for remaining in range(seconds, 0, -1):
            await broadcast_timer_update(game_id, remaining)
            try:
                await redis_client.set_timer(game_id, remaining)
            except Exception:
                pass
            await asyncio.sleep(1)

        # Broadcast 0 explicitly so clients know the countdown has ended
        await broadcast_timer_update(game_id, 0)

    # ── Main game loop ────────────────────────────────────────────────────────
    async def _game_loop(self, game_id: str):
        # Grace period: give players time to join after countdown ends.
        # The autoJoin HTTP request is triggered by timer_update(0) and
        # may arrive up to several seconds AFTER the countdown ends.
        # We wait here BEFORE opening the DB session so the join can commit.
        await asyncio.sleep(8)

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Game).where(Game.game_id == game_id))
            game = result.scalar_one_or_none()
            if not game:
                return

            # Re-read total_players from DB after the grace period — the join
            # commits to the DB, so we need the freshest value here.
            await db.refresh(game)

            # No players — finish quietly, do NOT auto-create next game.
            # A new game will be created on-demand when a player selects this stake.
            if game.total_players == 0:
                game.status = GameStatus.FINISHED
                await db.commit()
                print(f"Game {game_id} (stake={game.entry_fee}) has no players after grace period - finishing (no next game)")
                return

            # Mark ACTIVE
            print(f"Starting game {game_id} (stake={game.entry_fee}) with {game.total_players} players")
            game.status = GameStatus.ACTIVE
            game.started_at = datetime.utcnow()
            await db.commit()

            # Update Redis
            try:
                await redis_client.set_game_state(game_id, {
                    "status": GameStatus.ACTIVE.value,
                    "players": game.total_players,
                    "started_at": game.started_at.isoformat()
                })
            except Exception:
                pass

            await broadcast_game_started(game_id)

            game_manager = GameManager(db)

            while True:
                # Refresh game state from DB
                await db.refresh(game)

                # Stop if externally cancelled
                if game.status != GameStatus.ACTIVE:
                    print(f"Game {game_id} stopped externally")
                    break

                # Pop next number from the pre-shuffled deck
                number = await game_manager.call_number(game_id)
                if number is None:
                    # All 75 numbers called — no winner
                    print(f"Game {game_id}: all 75 numbers called, no winner")
                    await game_manager.finish_game(game_id, [])
                    await broadcast_player_won(game_id, [])
                    break

                letter = BingoGameEngine.get_number_category(number)
                print(f"Game {game_id}: Called {letter}-{number}")

                # ──────────────────────────────────────────────────────────────
                # PERFORMANCE FIX: Do NOT call mark_number_on_all_cards() here.
                # The number is already stored in game.called_numbers (DB) and
                # redis called-numbers list.  The frontend marks cards locally.
                # Server-side win detection reads called_numbers from DB and
                # re-checks each player's card only when needed.
                # ──────────────────────────────────────────────────────────────

                # Broadcast to frontend — clients mark their own cards
                await broadcast_number_called(game_id, number, letter)

                winners = await self._check_winners_fast(game_id, db)
                if winners:
                    print(f"BINGO! Game {game_id} has {len(winners)} winner(s)")

                    # Mark game finished immediately
                    await db.refresh(game)
                    game.status = GameStatus.FINISHED
                    game.finished_at = datetime.utcnow()
                    await db.commit()

                    winner_ids = [w.user_id for w in winners]
                    prize = await game_manager.finish_game(game_id, winner_ids)

                    # Build winner broadcast payload
                    winner_data = []
                    for w in winners:
                        u_res = await db.execute(select(User).where(User.id == w.user_id))
                        u = u_res.scalar_one_or_none()
                        winner_data.append({
                            "user_id":        w.user_id,
                            "username":       (u.username or u.first_name) if u else f"Player{w.user_id}",
                            "card_number":    w.card_number,
                            "card_data":      w.card_data,
                            "winning_pattern": w.winning_pattern,
                            "prize_amount":   prize or 0,
                        })

                    await broadcast_player_won(game_id, winner_data)
                    print(f"Game {game_id} finished - winner announced")
                    break

                # Wait before calling next number
                await asyncio.sleep(settings.GAME_INTERVAL_SECONDS)

        # Give players time to see winner screen before next game starts (synchronized with frontend 5s timer)
        await asyncio.sleep(4)
        await self._create_next_game(game_id)

    # ── Fast winner check (no per-number DB writes) ───────────────────────────
    async def _check_winners_fast(self, game_id: str, db) -> list:
        """
        Check all players for winning patterns WITHOUT marking numbers in DB.
        Numbers are read from game.called_numbers (already updated by call_number()).
        This replaces the O(N×600) DB-write approach.
        """
        from sqlalchemy.orm.attributes import flag_modified

        # Get called numbers from Redis (no DB write per number)
        result = await db.execute(select(Game).where(Game.game_id == game_id))
        game = result.scalar_one_or_none()
        if not game:
            return []

        called_list = await redis_client.get_called_numbers(game_id)
        called = set(called_list)

        # Get players who haven't won yet
        players_result = await db.execute(
            select(Player).where(
                Player.game_id == game.id,
                Player.has_won.is_(False),
            )
        )
        players = players_result.scalars().all()

        winners = []
        for player in players:
            # Recompute marked positions from called numbers (no DB write)
            marked = []
            card = player.card_data  # [[col0 nums], [col1 nums], ...]
            for col_idx in range(5):
                for row_idx in range(5):
                    num = card[col_idx][row_idx]
                    if num == 0 or num in called:          # 0 = FREE space
                        flat_idx = row_idx * 5 + col_idx
                        if flat_idx not in marked:
                            marked.append(flat_idx)

            has_won, pattern = BingoGameEngine.check_win(card, marked)
            if has_won:
                player.has_won = True
                player.winning_pattern = pattern
                player.marked_numbers = marked   # persist final state for winner
                flag_modified(player, "marked_numbers")
                winners.append(player)
                print(f"Player {player.user_id} won with pattern: {pattern}")

        if winners:
            await db.commit()

        return winners

    # ── Auto-create next game ─────────────────────────────────────────────────
    async def _create_next_game(self, old_game_id: str):
        try:
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(Game).where(Game.game_id == old_game_id))
                old = result.scalar_one_or_none()
                if not old:
                    return

                gm = GameManager(db)
                new_game = await gm.create_game(old.room, old.entry_fee)
                print(f"Next game created: {new_game.game_id} (stake={old.entry_fee})")

                # Notify all clients still connected to the old game room
                await ws_manager.broadcast_to_game(
                    {
                        "type": "next_game",
                        "data": {"game_id": new_game.game_id, "entry_fee": old.entry_fee},
                    },
                    old_game_id,
                )

                # Start countdown for the new game
                await self.start_countdown_loop(new_game.game_id)

        except Exception as e:
            print(f"Failed to create next game after {old_game_id}: {e}")


# Singleton
game_loop_manager = GameLoopManager()

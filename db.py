import sqlite3
import json
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

class Database:
    def __init__(self, db_path: str = "bingo.db"):
        self.db_path = db_path
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_db(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    balance REAL DEFAULT 0,
                    games_played INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Games table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'waiting',
                    entry_fee REAL NOT NULL,
                    total_pool REAL DEFAULT 0,
                    winner_id INTEGER,
                    called_numbers TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    finished_at TIMESTAMP
                )
            """)
            
            # Players table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    card TEXT NOT NULL,
                    marked TEXT DEFAULT '[]',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (game_id) REFERENCES games(id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(game_id, user_id)
                )
            """)
            
            # Transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    game_id INTEGER,
                    amount REAL NOT NULL,
                    tx_ref TEXT UNIQUE NOT NULL,
                    status TEXT DEFAULT 'pending',
                    type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (game_id) REFERENCES games(id)
                )
            """)

    # USER OPERATIONS
    def create_user(self, telegram_id: int, username: str = None) -> int:
        """Create a new user or return existing user id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO users (telegram_id, username)
                VALUES (?, ?)
            """, (telegram_id, username))
            
            cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
            return cursor.fetchone()[0]
    
    def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get user by telegram_id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_user_balance(self, telegram_id: int, amount: float):
        """Update user balance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET balance = balance + ? WHERE telegram_id = ?
            """, (amount, telegram_id))
    
    def increment_games_played(self, telegram_id: int):
        """Increment games played counter"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET games_played = games_played + 1 WHERE telegram_id = ?
            """, (telegram_id,))
    
    # GAME OPERATIONS
    def create_game(self, chat_id: int, entry_fee: float) -> int:
        """Create a new game"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO games (chat_id, status, entry_fee)
                VALUES (?, 'waiting', ?)
            """, (chat_id, entry_fee))
            return cursor.lastrowid
    
    def get_game(self, game_id: int) -> Optional[Dict[str, Any]]:
        """Get game by id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM games WHERE id = ?", (game_id,))
            row = cursor.fetchone()
            if row:
                game = dict(row)
                game['called_numbers'] = json.loads(game['called_numbers'])
                return game
            return None
    
    def get_active_game(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Get active or waiting game in chat"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM games 
                WHERE chat_id = ? AND status IN ('waiting', 'active')
                ORDER BY created_at DESC LIMIT 1
            """, (chat_id,))
            row = cursor.fetchone()
            if row:
                game = dict(row)
                game['called_numbers'] = json.loads(game['called_numbers'])
                return game
            return None
    
    def update_game_status(self, game_id: int, status: str):
        """Update game status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if status == 'active':
                cursor.execute("""
                    UPDATE games SET status = ?, started_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, game_id))
            elif status == 'finished':
                cursor.execute("""
                    UPDATE games SET status = ?, finished_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, game_id))
            else:
                cursor.execute("UPDATE games SET status = ? WHERE id = ?", (status, game_id))
    
    def add_called_number(self, game_id: int, number: int):
        """Add a called number to the game"""
        game = self.get_game(game_id)
        if game:
            called_numbers = game['called_numbers']
            called_numbers.append(number)
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE games SET called_numbers = ? WHERE id = ?
                """, (json.dumps(called_numbers), game_id))
    
    def set_winner(self, game_id: int, user_id: int):
        """Set game winner"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE games SET winner_id = ?, status = 'finished', 
                finished_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (user_id, game_id))
    
    # PLAYER OPERATIONS
    def add_player(self, game_id: int, user_id: int, card: List[List[int]]) -> bool:
        """Add player to game"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO players (game_id, user_id, card)
                    VALUES (?, ?, ?)
                """, (game_id, user_id, json.dumps(card)))
                
                # Update total pool
                game = self.get_game(game_id)
                cursor.execute("""
                    UPDATE games SET total_pool = total_pool + ? WHERE id = ?
                """, (game['entry_fee'], game_id))
                return True
        except sqlite3.IntegrityError:
            return False
    
    def get_players(self, game_id: int) -> List[Dict[str, Any]]:
        """Get all players in a game"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, u.telegram_id, u.username 
                FROM players p
                JOIN users u ON p.user_id = u.id
                WHERE p.game_id = ?
            """, (game_id,))
            players = []
            for row in cursor.fetchall():
                player = dict(row)
                player['card'] = json.loads(player['card'])
                player['marked'] = json.loads(player['marked'])
                players.append(player)
            return players
    
    def get_player(self, game_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """Get specific player in a game"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM players WHERE game_id = ? AND user_id = ?
            """, (game_id, user_id))
            row = cursor.fetchone()
            if row:
                player = dict(row)
                player['card'] = json.loads(player['card'])
                player['marked'] = json.loads(player['marked'])
                return player
            return None
    
    def update_player_marked(self, game_id: int, user_id: int, marked: List[int]):
        """Update player's marked numbers"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE players SET marked = ? WHERE game_id = ? AND user_id = ?
            """, (json.dumps(marked), game_id, user_id))
    
    # TRANSACTION OPERATIONS
    def create_transaction(self, user_id: int, amount: float, tx_ref: str, 
                          transaction_type: str, game_id: int = None) -> int:
        """Create a new transaction"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (user_id, game_id, amount, tx_ref, type)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, game_id, amount, tx_ref, transaction_type))
            return cursor.lastrowid
    
    def update_transaction_status(self, tx_ref: str, status: str):
        """Update transaction status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE transactions SET status = ? WHERE tx_ref = ?
            """, (status, tx_ref))
    
    def get_transaction(self, tx_ref: str) -> Optional[Dict[str, Any]]:
        """Get transaction by reference"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE tx_ref = ?", (tx_ref,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # LEADERBOARD
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top players by balance"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT username, balance, games_played 
                FROM users 
                ORDER BY balance DESC 
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

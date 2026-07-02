from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .models import GameStatus, TransactionStatus, TransactionType

# User Schemas
class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    phone_number: Optional[str] = None
    balance: float
    play_balance: float
    coins: int
    wins: int
    games_played: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Game Schemas
class GameCreate(BaseModel):
    room: str = "beginner"
    entry_fee: float
    max_players: int = 100

class GameResponse(BaseModel):
    id: int
    game_id: str
    status: GameStatus
    room: str
    entry_fee: float
    prize_pool: float
    total_players: int
    max_players: int
    called_numbers: List[int]
    current_number: Optional[int]
    winner_ids: List[int]
    countdown_seconds: int
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Player Schemas
class PlayerCreate(BaseModel):
    card_number: int = Field(..., ge=1, le=600)

class PlayerResponse(BaseModel):
    id: int
    user_id: int
    game_id: int
    card_number: int
    card_data: List[List[int]]
    marked_numbers: List[int]
    has_won: bool
    winning_pattern: Optional[str]
    joined_at: datetime
    
    class Config:
        from_attributes = True

# Transaction Schemas
class TransactionCreate(BaseModel):
    amount: float
    type: TransactionType
    payment_method: Optional[str] = None

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    game_id: Optional[int]
    amount: float
    tx_ref: str
    status: TransactionStatus
    type: TransactionType
    payment_method: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# WebSocket Messages
class WSMessage(BaseModel):
    type: str
    data: dict

class CardSelectedMessage(BaseModel):
    card_number: int
    user_id: int
    username: Optional[str]

class TimerUpdateMessage(BaseModel):
    seconds: int

class NumberCalledMessage(BaseModel):
    number: int
    category: str  # B, I, N, G, O

class PlayerWonMessage(BaseModel):
    user_id: int
    username: Optional[str]
    card_number: int
    winning_pattern: str
    prize_amount: float


# Leaderboard Schema
class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: Optional[str]
    total_wins: int
    total_earnings: float
    
    class Config:
        from_attributes = True

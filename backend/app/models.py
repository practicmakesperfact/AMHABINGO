from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from .database import Base

class GameStatus(str, enum.Enum):
    WAITING = "waiting"
    COUNTDOWN = "countdown"
    ACTIVE = "active"
    FINISHED = "finished"

class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

class TransactionType(str, enum.Enum):
    ENTRY_FEE = "entry_fee"
    PAYOUT = "payout"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    balance = Column(Float, default=0.0)
    wins = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    players = relationship("Player", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(String, unique=True, nullable=False, index=True)
    status = Column(SQLEnum(GameStatus), default=GameStatus.WAITING)
    room = Column(String, default="beginner")  # beginner, pro, vip
    entry_fee = Column(Float, nullable=False)
    prize_pool = Column(Float, default=0.0)
    total_players = Column(Integer, default=0)
    max_players = Column(Integer, default=100)
    called_numbers = Column(JSON, default=list)
    current_number = Column(Integer, nullable=True)
    winner_ids = Column(JSON, default=list)  # Support multiple winners
    countdown_seconds = Column(Integer, default=60)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    players = relationship("Player", back_populates="game", cascade="all, delete-orphan")

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    card_number = Column(Integer, nullable=False)  # 1-600
    card_data = Column(JSON, nullable=False)  # 5x5 bingo card
    marked_numbers = Column(JSON, default=list)
    has_won = Column(Boolean, default=False)
    winning_pattern = Column(String, nullable=True)  # row, column, diagonal
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="players")
    game = relationship("Game", back_populates="players")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=True)
    amount = Column(Float, nullable=False)
    tx_ref = Column(String, unique=True, nullable=False, index=True)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    type = Column(SQLEnum(TransactionType), nullable=False)
    payment_method = Column(String, nullable=True)  # chapa, telebirr, etc
    extra_data = Column(JSON, default=dict)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transactions")

class Leaderboard(Base):
    __tablename__ = "leaderboard"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    total_wins = Column(Integer, default=0)
    total_earnings = Column(Float, default=0.0)
    rank = Column(Integer, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

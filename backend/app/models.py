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
    TRANSFER = "transfer"
    REFERRAL_REWARD = "referral_reward"
    BONUS_CONVERSION = "bonus_conversion"

class DepositStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    APPROVED = "approved"
    REJECTED = "rejected"

class WithdrawalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    COMPLETED = "completed"

class PaymentMethod(str, enum.Enum):
    TELEBIRR = "telebirr"
    CBEBIRR = "cbebirr"
    BANK_TRANSFER = "bank_transfer"
    MANUAL = "manual"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    phone_number = Column(String, nullable=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    balance = Column(Float, default=0.0)
    play_balance = Column(Float, default=0.0)
    coins = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    games_played = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    players = relationship("Player", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

class Cartela(Base):
    """
    Permanent cartela storage - 600 pre-generated bingo cards.
    Each cartela has a unique 5x5 grid that never changes.
    """
    __tablename__ = "cartelas"
    
    id = Column(Integer, primary_key=True, index=True)
    cartela_number = Column(Integer, unique=True, nullable=False, index=True)  # 1-600
    card_data = Column(JSON, nullable=False)  # Permanent 5x5 grid
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
    remaining_numbers = Column(JSON, default=list)  # Shuffled deck for pop() method
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
    card_number = Column(Integer, nullable=False)  # 1-600 (references Cartela.cartela_number)
    card_data = Column(JSON, nullable=False)  # Copy of cartela's 5x5 grid for this game
    marked_numbers = Column(JSON, default=list)
    has_won = Column(Boolean, default=False)
    winning_pattern = Column(String, nullable=True)  # row_0, col_1, diagonal_lr, four_corner, blackout
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
    payment_method = Column(String, nullable=True)  # telebirr (via bot)
    extra_data = Column(JSON, default=dict)
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


class Deposit(Base):
    """
    Deposit requests from users.
    Flow: pending → verified (receipt submitted) → approved/rejected (by admin)
    """
    __tablename__ = "deposits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.TELEBIRR)
    status = Column(SQLEnum(DepositStatus), default=DepositStatus.PENDING, index=True)
    
    # Receipt data (parsed from Telebirr message)
    receipt_data = Column(JSON, nullable=True)  # {sender_name, sender_phone, tx_ref, amount, date}
    receipt_message = Column(String, nullable=True)  # Original Telebirr message
    
    # Admin actions
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_notes = Column(String, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Tracking
    tx_ref = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="deposits")
    admin = relationship("User", foreign_keys=[admin_id])


class Withdrawal(Base):
    """
    Withdrawal requests from users.
    Flow: pending → approved/rejected (by admin) → processing → completed
    """
    __tablename__ = "withdrawals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    phone_number = Column(String, nullable=False)  # Destination phone for Telebirr
    payment_method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.TELEBIRR)
    status = Column(SQLEnum(WithdrawalStatus), default=WithdrawalStatus.PENDING, index=True)
    
    # Admin actions
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    admin_notes = Column(String, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Payment proof
    payment_proof = Column(String, nullable=True)  # Screenshot or transaction ID
    
    # Tracking
    tx_ref = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="withdrawals")
    admin = relationship("User", foreign_keys=[admin_id])


class Transfer(Base):
    """
    User-to-user balance transfers.
    Instant transfer between registered users.
    """
    __tablename__ = "transfers"
    
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    
    # Optional message
    message = Column(String, nullable=True)
    
    # Tracking
    tx_ref = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], backref="transfers_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], backref="transfers_received")


class Referral(Base):
    """
    Referral tracking and rewards.
    When a new user registers via referral link, referrer gets reward.
    """
    __tablename__ = "referrals"
    
    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Reward tracking
    reward_amount = Column(Float, default=5.0)  # 5 ETB default
    reward_paid = Column(Boolean, default=False)
    reward_paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id], backref="referrals_made")
    referee = relationship("User", foreign_keys=[referee_id], backref="referred_by")


class PaymentAccount(Base):
    """
    Admin-managed payment accounts for deposits.
    Users deposit to these Telebirr numbers.
    """
    __tablename__ = "payment_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_name = Column(String, nullable=False)  # "Main Telebirr Account"
    account_number = Column(String, nullable=False)  # Telebirr phone number
    payment_method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.TELEBIRR)
    
    # Account details
    account_holder_name = Column(String, nullable=False)
    account_holder_phone = Column(String, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    daily_limit = Column(Float, nullable=True)  # Optional daily deposit limit
    
    # Tracking
    total_deposits = Column(Float, default=0.0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AdminLog(Base):
    """
    Audit log for admin actions.
    Tracks all deposits/withdrawals approved/rejected by admins.
    """
    __tablename__ = "admin_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String, nullable=False)  # approve_deposit, reject_withdrawal, etc.
    resource_type = Column(String, nullable=False)  # deposit, withdrawal, user, etc.
    resource_id = Column(Integer, nullable=False)
    details = Column(JSON, nullable=True)  # Additional context
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    admin = relationship("User", foreign_keys=[admin_id])


class Notification(Base):
    """
    In-app notifications for users.
    Winners, deposit approvals, withdrawal updates, etc.
    """
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Notification content
    type = Column(String, nullable=False)  # winner, deposit_approved, withdrawal_rejected, etc.
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    
    # Status
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Optional action link
    action_url = Column(String, nullable=True)
    
    # Tracking
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", backref="notifications")

"""
Database Module

This module handles SQLite database operations for:
- Session management (conversation history)
- Scheduled tasks storage
- Message history

Uses SQLAlchemy ORM for type-safe database operations.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, Column, String, DateTime, Text, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from src.config import config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# SQLAlchemy base class for models
Base = declarative_base()


class ConversationSession(Base):
    """
    Represents a conversation session with a user.
    
    A session groups related messages together and maintains context
    across multiple interactions.
    
    Attributes:
        session_id: Unique identifier for the session (primary key)
        user_id: Slack user ID
        channel_id: Slack channel ID (for channel conversations)
        thread_ts: Slack thread timestamp (for threaded conversations)
        created_at: When the session was created
        updated_at: When the session was last updated
        is_active: Whether the session is currently active
    """
    __tablename__ = "conversation_sessions"
    
    session_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    channel_id = Column(String, nullable=True)
    thread_ts = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class Message(Base):
    """
    Represents a single message in a conversation.
    
    Messages are linked to sessions and store the full conversation history
    for context and debugging.
    
    Attributes:
        id: Auto-incrementing primary key
        session_id: Foreign key to conversation_sessions
        role: Message role (user, assistant, system, tool)
        content: Message content
        timestamp: When the message was created
        msg_metadata: Additional metadata (JSON string)
    """
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    msg_metadata = Column(Text, nullable=True)  # JSON string for additional data


class ScheduledTask(Base):
    """
    Represents a scheduled task (reminder or message).
    
    Tasks can be one-time or recurring (using cron expressions).
    
    Attributes:
        task_id: Unique identifier for the task (primary key)
        user_id: Slack user ID who created the task
        channel_id: Slack channel ID where task should execute
        task_type: Type of task (reminder, message, etc.)
        message: Message to send when task executes
        schedule_time: When to execute (for one-time tasks)
        cron_expression: Cron expression (for recurring tasks)
        is_recurring: Whether the task repeats
        is_active: Whether the task is active
        created_at: When the task was created
        last_run: When the task last executed
    """
    __tablename__ = "scheduled_tasks"
    
    task_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    channel_id = Column(String, nullable=False)
    task_type = Column(String, nullable=False)  # reminder, message, etc.
    message = Column(Text, nullable=False)
    schedule_time = Column(DateTime, nullable=True)  # For one-time tasks
    cron_expression = Column(String, nullable=True)  # For recurring tasks
    is_recurring = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_run = Column(DateTime, nullable=True)


# Database engine and session factory
engine = None
SessionLocal = None


def initialize_database() -> None:
    """
    Initialize the database connection and create tables.
    
    This function should be called once at application startup.
    It creates the database file if it doesn't exist and sets up
    all tables defined in the models.
    """
    global engine, SessionLocal
    
    # Ensure data directory exists
    db_path = Path(config.database_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create engine
    database_url = f"sqlite:///{config.database_path}"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        echo=config.log_level == "DEBUG"  # Log SQL queries in debug mode
    )
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    logger.info(f"Database initialized at {config.database_path}")


def get_db_session() -> Session:
    """
    Get a database session.
    
    This function creates a new session that should be closed after use.
    Use in a context manager for automatic cleanup:
    
    Example:
        >>> with get_db_session() as db:
        >>>     session = db.query(ConversationSession).first()
    
    Returns:
        Session: SQLAlchemy session object
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    
    return SessionLocal()


def get_or_create_session(
    user_id: str,
    channel_id: Optional[str] = None,
    thread_ts: Optional[str] = None
) -> str:
    """
    Get an existing session or create a new one.
    
    Sessions are identified by user_id, channel_id, and thread_ts.
    If an active session exists with these parameters, it's returned.
    Otherwise, a new session is created.
    
    Args:
        user_id: Slack user ID
        channel_id: Slack channel ID (optional)
        thread_ts: Slack thread timestamp (optional)
        
    Returns:
        str: Session ID
    """
    with get_db_session() as db:
        # Try to find existing active session
        query = db.query(ConversationSession).filter(
            ConversationSession.user_id == user_id,
            ConversationSession.is_active == True
        )
        
        if channel_id:
            query = query.filter(ConversationSession.channel_id == channel_id)
        if thread_ts:
            query = query.filter(ConversationSession.thread_ts == thread_ts)
        
        session = query.first()
        
        if session:
            # Update timestamp
            session.updated_at = datetime.utcnow()
            db.commit()
            logger.debug(f"Using existing session: {session.session_id}")
            return session.session_id
        
        # Create new session
        session_id = f"session_{user_id}_{datetime.utcnow().timestamp()}"
        new_session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            channel_id=channel_id,
            thread_ts=thread_ts
        )
        db.add(new_session)
        db.commit()
        
        logger.info(f"Created new session: {session_id}")
        return session_id


def add_message(
    session_id: str,
    role: str,
    content: str,
    msg_metadata: Optional[str] = None
) -> None:
    """
    Add a message to a session.
    
    Args:
        session_id: Session ID to add message to
        role: Message role (user, assistant, system, tool)
        content: Message content
        msg_metadata: Optional metadata (JSON string)
    """
    with get_db_session() as db:
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            msg_metadata=msg_metadata
        )
        db.add(message)
        db.commit()
        
        logger.debug(f"Added {role} message to session {session_id}")


def get_session_history(session_id: str, limit: int = 50) -> list[dict]:
    """
    Get message history for a session.
    
    Args:
        session_id: Session ID to retrieve history for
        limit: Maximum number of messages to retrieve (default: 50)
        
    Returns:
        list[dict]: List of messages in chronological order
            Each message is a dict with keys: role, content, timestamp
    """
    with get_db_session() as db:
        messages = (
            db.query(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.timestamp.asc())
            .limit(limit)
            .all()
        )
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in messages
        ]


def clear_session(session_id: str) -> None:
    """
    Clear a session and its messages.
    
    This marks the session as inactive and can be used to reset
    the conversation context.
    
    Args:
        session_id: Session ID to clear
    """
    with get_db_session() as db:
        # Mark session as inactive
        session = db.query(ConversationSession).filter(
            ConversationSession.session_id == session_id
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
            logger.info(f"Cleared session: {session_id}")


if __name__ == "__main__":
    # Test database operations
    initialize_database()
    
    # Create a test session
    session_id = get_or_create_session("U123456", "C789012")
    print(f"Session ID: {session_id}")
    
    # Add some messages
    add_message(session_id, "user", "Hello!")
    add_message(session_id, "assistant", "Hi! How can I help you?")
    
    # Get history
    history = get_session_history(session_id)
    print(f"History: {history}")
    
    # Clear session
    clear_session(session_id)
    print("Session cleared")

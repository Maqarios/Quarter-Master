# Bot/db/database.py
"""
Database configuration and utilities for Quarter Master Bot.

This module provides database connection management, session handling, and utility
functions for database operations using SQLAlchemy ORM. It supports both development
and production environments with appropriate configurations.

Environment Variables:
    DATABASE_URL: The database connection URL
    ENVIRONMENT: The environment mode ('production' for production settings)
"""

import logging
from contextlib import contextmanager

from config import settings
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

log = logging.getLogger(__name__)

# Configure the database engine and session
db_engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=not settings.is_production,
    connect_args={"sslmode": "require"} if settings.is_production else {},
)
db_session = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)


# Define the base class for declarative models
class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy declarative models.

    All database models should inherit from this class to ensure proper
    table creation and ORM functionality.
    """

    pass


# Utility function to check database connection
def check_db_connection():
    """
    Check if the database connection is working properly.

    Attempts to connect to the database and execute a simple query
    to verify connectivity.

    Returns:
        bool: True if connection is successful, False otherwise.

    Example:
        >>> if check_db_connection():
        ...     print("Database is connected")
        ... else:
        ...     print("Database connection failed")
    """
    try:
        # Attempt to connect and execute a simple query
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        log.error(f"Database connection failed: {e}")
        return False


# Utility context manager for database sessions (Automatic Transaction Management)
@contextmanager
def get_db_context():
    """
    Context manager for database sessions with automatic transaction management.

    This is the recommended pattern for Discord bot commands and synchronous
    operations where you want automatic commit/rollback handling.

    Provides a database session that automatically commits on success or
    rolls back on exceptions. The session is always closed regardless of
    the outcome.

    Yields:
        Session: SQLAlchemy database session

    Raises:
        Exception: Re-raises any database-related exceptions after rollback

    Example:
        >>> with get_db_context() as db:
        ...     user = User(name="John")
        ...     db.add(user)
        ...     # Automatically commits on exit

    Note:
        Use this for Discord bot commands. For FastAPI routes, use get_db() instead.
    """
    # Create a new database session
    db = db_session()
    try:
        # return the session to the caller then commit if no exceptions
        yield db
        db.commit()
    except Exception as e:
        # Log the error and rollback the transaction
        log.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        # Close the database session
        db.close()


# Utility generator for database sessions (Manual Transaction Control)
def get_db():
    """
    Generator function for database sessions with manual transaction control.

    This is the recommended pattern for FastAPI route handlers where you need
    explicit control over transactions and want to use dependency injection.

    Provides a database session that requires manual commit/rollback handling.
    The session is automatically closed after use. This pattern integrates
    seamlessly with FastAPI's Depends() system.

    Yields:
        Session: SQLAlchemy database session

    Example:
        >>> from fastapi import APIRouter, Depends
        >>> from sqlalchemy.orm import Session
        >>>
        >>> router = APIRouter()
        >>>
        >>> @router.post("/users")
        >>> async def create_user(
        ...     name: str,
        ...     db: Session = Depends(get_db)
        ... ):
        ...     try:
        ...         user = User(name=name)
        ...         db.add(user)
        ...         db.commit()
        ...         db.refresh(user)
        ...         return user
        ...     except Exception:
        ...         db.rollback()
        ...         raise

    Note:
        Use this for FastAPI routes. For Discord bot commands, use get_db_context() instead.
    """
    db = db_session()
    try:
        yield db
    finally:
        db.close()

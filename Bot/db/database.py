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
import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production"

log = logging.getLogger(__name__)

if DB_URL is None:
    log.error("DATABASE_URL environment variable is not set")
    raise ValueError("DATABASE_URL environment variable is not set")

# Configure the database engine and session
db_engine = create_engine(
    DB_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=not IS_PRODUCTION,  # True for debugging
    connect_args={"sslmode": "require"} if IS_PRODUCTION else {},
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


# Utility context manager for database sessions (Transaction Management)
@contextmanager
def get_db_context():
    """
    Context manager for database sessions with automatic transaction management.

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


# Utility generator for database sessions (Manual Control)
def get_db():
    """
    Generator function for database sessions with manual transaction control.

    Provides a database session that requires manual commit/rollback handling.
    The session is automatically closed after use. This is useful when you
    need fine-grained control over transactions.

    Yields:
        Session: SQLAlchemy database session

    Example:
        >>> for db in get_db():
        ...     try:
        ...         user = User(name="John")
        ...         db.add(user)
        ...         db.commit()
        ...     except Exception:
        ...         db.rollback()
        ...         raise
    """
    db = db_session()
    try:
        yield db
    finally:
        db.close()

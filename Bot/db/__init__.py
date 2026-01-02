# Bot/db/__init__.py
"""Database package for the Quarter Master Bot."""

from .database import Base, check_db_connection, db_engine, get_db, get_db_context

__all__ = [
    "Base",
    "db_engine",
    "get_db_context",  # For Discord bot commands (automatic transactions)
    "get_db",  # For FastAPI routes (manual transactions)
    "check_db_connection",
]

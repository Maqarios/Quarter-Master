"""
API Key model for Quarter Master Bot authentication system.

This module defines the APIKey SQLAlchemy model used for managing API keys
for Discord users. It provides secure authentication and authorization
capabilities with proper key lifecycle management.

Key Features:
    - Secure hashed key storage (never plaintext)
    - Discord user association via discord_id
    - Automatic timestamp tracking (created, last_used, revoked)
    - Soft deletion with revoked_at timestamps
    - Optimized PostgreSQL partial indexing for active keys
    - Timezone-aware datetime handling

Security Notes:
    - Always hash API keys using bcrypt or Argon2 before storage
    - Never log or expose plaintext API keys
    - Keys cannot be reactivated once revoked - create new keys instead

Usage Example:
    >>> from database import get_db_context
    >>> from models.api_key import APIKey
    >>>
    >>> with get_db_context() as db:
    ...     # Create new API key
    ...     key = APIKey(
    ...         discord_id=123456789,
    ...         hashed_key="$2b$12$...",  # bcrypt hash
    ...         description="My Bot Key"
    ...     )
    ...     db.add(key)
    ...     # Auto-commits on context exit
"""

import uuid
from datetime import datetime, timezone
from time import time

from database import Base
from sqlalchemy import BigInteger, Column, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class APIKey(Base):
    """
    API Key model for authentication and authorization.

    This model stores API keys for Discord users, providing secure authentication
    for API endpoints. Keys are stored in hashed format and include metadata
    for tracking usage and managing lifecycle.

    Attributes:
        id (UUID): Primary key, auto-generated UUID4
        discord_id (int): Discord user ID of the key owner
        hashed_key (str): Bcrypt/Argon2 hashed API key (never plaintext)
        description (str, optional): User-provided label for the key
        created_at (datetime): Timestamp when the key was created
        last_used_at (datetime, optional): Last time this key was used
        revoked_at (datetime, optional): When the key was revoked (NULL = active)

    Note:
        - API keys should never be stored in plaintext
        - Use bcrypt or Argon2 for hashing
        - Partial index optimizes queries for active keys only
    """

    __tablename__ = "api_keys"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Owner identification
    discord_id = Column(
        BigInteger,
        nullable=False,
        index=True,
        comment="Discord user ID of the key owner",
    )

    # Hashed API key (never store plaintext!)
    hashed_key = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="Bcrypt/Argon2 hashed API key",
    )

    # Optional description/label
    description = Column(
        String(255),
        nullable=True,
        comment="User-provided label for the key",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    last_used_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
        comment="Last time this key was used for authentication",
    )

    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the key was revoked (NULL = active)",
    )

    # Composite index for efficient queries
    __table_args__ = (
        Index(
            "ix_api_keys_discord_id_active",
            "discord_id",
            "revoked_at",
            postgresql_where="revoked_at IS NULL",  # Fixed PostgreSQL syntax
        ),
    )

    def __repr__(self) -> str:
        """
        Return a string representation of the APIKey instance.

        Returns:
            str: Human-readable representation showing ID, Discord ID, and status
        """
        status = "Active" if self.is_active else "Revoked"
        return f"<APIKey(id={self.id}, discord_id={self.discord_id}, status={status})>"

    @property
    def is_active(self) -> bool:
        """Check if the key is currently active (not revoked)."""
        return self.revoked_at is None

    def revoke(self) -> None:
        """
        Revoke this API key by setting the revoked_at timestamp.

        Sets the revoked_at field to the current UTC time if the key is currently
        active. Once revoked, a key cannot be reactivated - a new key must be created.

        Note:
            This method only marks the key as revoked in memory. You must commit
            the database session to persist the change.
        """
        if self.is_active:
            self.revoked_at = datetime.now(timezone.utc)  # Use timezone-aware UTC

    def update_last_used(self) -> None:
        """
        Update the last_used_at timestamp to the current UTC time.

        This method should be called whenever the API key is successfully used
        for authentication to track usage patterns and detect inactive keys.

        Note:
            This method only updates the timestamp in memory. You must commit
            the database session to persist the change.
        """
        self.last_used_at = datetime.now(timezone.utc)  # Use timezone-aware UTC

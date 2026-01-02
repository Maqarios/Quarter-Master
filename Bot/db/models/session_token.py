# Bot/db/models/session_token.py
"""
Session Token model for Quarter Master Bot temporary authentication.

This module defines the SessionToken SQLAlchemy model used for managing
temporary authentication tokens for API access. Session tokens provide
time-limited access after initial API key validation.

Key Features:
    - Secure hashed token storage (never plaintext)
    - Foreign key relationship to APIKey with cascade deletion
    - Automatic expiration handling with configurable TTL
    - Usage tracking and security audit trail
    - Soft revocation with revoked_at timestamps
    - Optimized PostgreSQL partial indexing for active tokens
    - Timezone-aware datetime handling

Security Notes:
    - Always hash session tokens using bcrypt before storage
    - Never log or expose plaintext tokens
    - Tokens expire automatically based on expires_at timestamp
    - Tokens are deleted when parent API key is deleted (CASCADE)

Usage Example:
    >>> from db import get_db_context
    >>> from models import SessionToken
    >>> from datetime import datetime, timedelta, timezone
    >>>
    >>> with get_db_context() as db:
    ...     # Create new session token
    ...     token = SessionToken(
    ...         api_key_id=api_key.id,
    ...         hashed_token="$2b$12$...",  # bcrypt hash
    ...         expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    ...         ip_address="192.168.1.1",
    ...         user_agent="Mozilla/5.0..."
    ...     )
    ...     db.add(token)
    ...     # Auto-commits on context exit
"""

import uuid
from datetime import datetime, timezone

from db import Base
from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class SessionToken(Base):
    """
    Session Token model for temporary API authentication.

    This model stores temporary session tokens that provide time-limited access
    after initial API key validation. Tokens reduce the need to transmit API keys
    on every request and enable better security through short expiration windows.

    Attributes:
        id (UUID): Primary key, auto-generated UUID4
        api_key_id (UUID): Foreign key to the parent API key
        hashed_token (str): Bcrypt hashed session token (never plaintext)
        created_at (datetime): Timestamp when the token was created
        expires_at (datetime): When the token expires and becomes invalid
        last_used_at (datetime, optional): Last time this token was used
        revoked_at (datetime, optional): Manual revocation timestamp (NULL = active)
        ip_address (str, optional): IP address that created the token
        user_agent (str, optional): User agent string from token creation
        api_key (APIKey): Relationship to the parent API key

    Note:
        - Session tokens should never be stored in plaintext
        - Use bcrypt for hashing (consistent with API keys)
        - Tokens are automatically deleted when parent API key is deleted
        - Partial indexes optimize queries for active tokens only
    """

    __tablename__ = "session_tokens"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Foreign key to api_keys
    api_key_id = Column(
        UUID(as_uuid=True),
        ForeignKey("api_keys.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="API key that generated this session token",
    )

    # Hashed token value (never store plaintext!)
    hashed_token = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="Bcrypt hashed session token",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Token expiration timestamp",
    )

    last_used_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
        comment="Last time this token was used for authentication",
    )

    revoked_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Manual revocation timestamp (NULL = active)",
    )

    # Security audit metadata
    ip_address = Column(
        String(45),  # IPv6 max length
        nullable=True,
        comment="IP address that created this token",
    )

    user_agent = Column(
        String(255),
        nullable=True,
        comment="User agent string from token creation",
    )

    # Relationship to APIKey
    api_key = relationship("APIKey", back_populates="session_tokens")

    # Composite partial indexes for efficient queries
    __table_args__ = (
        Index(
            "ix_session_tokens_expires_at_active",
            "expires_at",
            "revoked_at",
            postgresql_where="revoked_at IS NULL",
        ),
        Index(
            "ix_session_tokens_api_key_active",
            "api_key_id",
            "revoked_at",
            postgresql_where="revoked_at IS NULL",
        ),
    )

    def __repr__(self) -> str:
        """
        Return a string representation of the SessionToken instance.

        Returns:
            str: Human-readable representation showing ID, API key ID, and status
        """
        status = "Valid" if self.is_valid else "Invalid/Expired"
        return f"<SessionToken(id={self.id}, api_key_id={self.api_key_id}, status={status})>"

    @property
    def is_valid(self) -> bool:
        """
        Check if the token is active and not expired.

        Returns:
            bool: True if token is not revoked and not past expiration time
        """
        now = datetime.now(timezone.utc)
        return bool(self.revoked_at is None and self.expires_at > now)

    @property
    def is_expired(self) -> bool:
        """
        Check if the token has passed its expiration time.

        Returns:
            bool: True if current time is past expires_at timestamp
        """
        return bool(datetime.now(timezone.utc) > self.expires_at)

    def revoke(self) -> None:
        """
        Revoke this session token by setting the revoked_at timestamp.

        Sets the revoked_at field to the current UTC time if the token is currently
        active. Once revoked, a token cannot be reactivated - a new token must be created.

        Note:
            This method only marks the token as revoked in memory. You must commit
            the database session to persist the change.
        """
        if self.revoked_at is None:
            self.revoked_at = datetime.now(timezone.utc)  # Use timezone-aware UTC

    def update_last_used(self) -> None:
        """
        Update the last_used_at timestamp to the current UTC time.

        This method should be called whenever the session token is successfully used
        for authentication to track usage patterns and detect suspicious activity.

        Note:
            This method only updates the timestamp in memory. You must commit
            the database session to persist the change.
        """
        self.last_used_at = datetime.now(timezone.utc)  # Use timezone-aware UTC

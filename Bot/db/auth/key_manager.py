"""
API Key Management Module for Quarter Master Bot.

This module provides secure API key generation, hashing, verification, and management
functionality for the Quarter Master Discord bot. It implements industry-standard
security practices including bcrypt hashing with salt and secure random key generation.

Key Features:
    - Cryptographically secure API key generation using secrets module
    - Bcrypt-based key hashing with configurable rounds (default: 12)
    - Input validation and sanitization for all operations
    - Comprehensive error handling with SQLAlchemy integration
    - Rate limiting considerations and performance optimization notes

Security Considerations:
    - Keys are hashed using bcrypt with salt before storage
    - Original plaintext keys are never stored in the database
    - Input validation prevents common attack vectors
    - Comprehensive logging for security monitoring

Usage Example:
    ```python
    # Create a new API key
    plaintext_key, api_key_record = create_api_key(db, discord_id=12345)

    # Authenticate a provided key
    authenticated_user = authenticate_key(db, provided_key)

    # Revoke an existing key
    success = revoke_api_key(db, key_id="some-id", discord_id=12345)
    ```

Author: Quarter Master Bot Development Team
Version: 1.0.0
Dependencies: bcrypt, sqlalchemy, secrets
"""

import logging
import re
import secrets
from typing import Optional, Tuple

import bcrypt
from models.api_key import APIKey
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

log = logging.getLogger(__name__)

# Constants
DEFAULT_KEY_PREFIX = "qm"
DEFAULT_KEY_LENGTH = 32
MIN_KEY_LENGTH = 16
MAX_KEY_LENGTH = 64
BCRYPT_ROUNDS = 12
API_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+_[a-zA-Z0-9_-]+$")


def generate_api_key(
    prefix: str = DEFAULT_KEY_PREFIX, length: int = DEFAULT_KEY_LENGTH
) -> str:
    """
    Generate a cryptographically secure API key.

    Args:
        prefix: Key prefix (default: "qm")
        length: Random portion length (default: 32, min: 16, max: 64)

    Returns:
        Generated API key in format: prefix_randomstring

    Raises:
        ValueError: If parameters are invalid
    """
    if not prefix or not isinstance(prefix, str) or len(prefix.strip()) == 0:
        raise ValueError("Prefix must be a non-empty string")

    if (
        not isinstance(length, int)
        or length < MIN_KEY_LENGTH
        or length > MAX_KEY_LENGTH
    ):
        raise ValueError(
            f"Length must be between {MIN_KEY_LENGTH} and {MAX_KEY_LENGTH}"
        )

    # Sanitize prefix to contain only alphanumeric and underscores
    clean_prefix = re.sub(r"[^a-zA-Z0-9_]", "", prefix.strip())
    if not clean_prefix:
        raise ValueError("Prefix contains no valid characters")

    random_key = secrets.token_urlsafe(length)
    return f"{clean_prefix}_{random_key}"


def hash_api_key(api_key: str) -> str:
    """
    Hash an API key using bcrypt.

    Args:
        api_key: The plaintext API key to hash

    Returns:
        Base64-encoded bcrypt hash

    Raises:
        ValueError: If api_key is invalid
    """
    if not api_key or not isinstance(api_key, str) or len(api_key.strip()) == 0:
        raise ValueError("API key must be a non-empty string")

    if not API_KEY_PATTERN.match(api_key.strip()):
        raise ValueError("API key format is invalid")

    salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(api_key.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_api_key(provided_key: str, hashed_key: str) -> bool:
    """
    Verify a provided key against its hash.

    Args:
        provided_key: The plaintext key to verify
        hashed_key: The stored bcrypt hash

    Returns:
        True if key matches, False otherwise
    """
    if not provided_key or not hashed_key:
        return False

    if not isinstance(provided_key, str) or not isinstance(hashed_key, str):
        return False

    try:
        return bcrypt.checkpw(provided_key.encode("utf-8"), hashed_key.encode("utf-8"))
    except Exception as e:
        log.error(f"Error verifying API key: {e}")
        return False


def create_api_key(
    db: Session, discord_id: int, description: Optional[str] = None
) -> Tuple[str, APIKey]:
    """
    Create a new API key for a Discord user.

    Args:
        db: Database session
        discord_id: Discord user ID
        description: Optional key description

    Returns:
        Tuple of (plaintext_key, api_key_record)

    Raises:
        ValueError: If discord_id is invalid
        SQLAlchemyError: If database operation fails
    """
    if not isinstance(discord_id, int) or discord_id <= 0:
        raise ValueError("Discord ID must be a positive integer")

    if description is not None and (
        not isinstance(description, str) or len(description) > 255
    ):
        raise ValueError("Description must be a string with max 255 characters")

    try:
        # Generate plaintext key
        plaintext_key = generate_api_key()

        # Hash the key for storage
        hashed = hash_api_key(plaintext_key)

        # Create database record
        api_key_record = APIKey(
            discord_id=discord_id,
            hashed_key=hashed,
            description=description.strip() if description else None,
        )

        db.add(api_key_record)
        db.flush()  # Get the ID without committing

        log.info(f"Created API key {api_key_record.id} for Discord user {discord_id}")
        return plaintext_key, api_key_record

    except SQLAlchemyError as e:
        log.error(f"Database error creating API key for user {discord_id}: {e}")
        raise


def revoke_api_key(db: Session, key_id: str, discord_id: int) -> bool:
    """
    Revoke an API key.

    Args:
        db: Database session
        key_id: ID of the key to revoke
        discord_id: Discord user ID (for authorization)

    Returns:
        True if key was revoked, False if not found/already revoked

    Raises:
        ValueError: If parameters are invalid
        SQLAlchemyError: If database operation fails
    """
    if not isinstance(discord_id, int) or discord_id <= 0:
        raise ValueError("Discord ID must be a positive integer")

    if not key_id or not isinstance(key_id, str):
        raise ValueError("Key ID must be a non-empty string")

    try:
        api_key = (
            db.query(APIKey)
            .filter(
                APIKey.id == key_id,
                APIKey.discord_id == discord_id,
                APIKey.revoked_at.is_(None),  # type: ignore
            )
            .first()
        )

        if not api_key:
            log.warning(
                f"Key {key_id} not found or already revoked for user {discord_id}"
            )
            return False

        api_key.revoke()
        db.flush()

        log.info(f"Revoked API key {key_id} for Discord user {discord_id}")
        return True

    except SQLAlchemyError as e:
        log.error(f"Database error revoking API key {key_id}: {e}")
        raise


def authenticate_key(db: Session, provided_key: str) -> Optional[APIKey]:
    """
    Authenticate an API key and return the associated record.

    Args:
        db: Database session
        provided_key: The API key to authenticate

    Returns:
        APIKey record if authentication successful, None otherwise

    Note: This function checks all active keys. Consider adding an index
    on a key prefix or implementing key lookup optimization for large datasets.
    """
    if not provided_key or not isinstance(provided_key, str):
        log.warning("Authentication attempted with invalid key format")
        return None

    provided_key = provided_key.strip()
    if not API_KEY_PATTERN.match(provided_key):
        log.warning("Authentication attempted with malformed key")
        return None

    try:
        # Get all active keys (we need to check each hash)
        # TODO: For better performance with many keys, consider adding a prefix index
        active_keys = db.query(APIKey).filter(APIKey.revoked_at.is_(None)).all()  # type: ignore

        for api_key in active_keys:
            if verify_api_key(provided_key, str(api_key.hashed_key)):
                # Update last used timestamp
                api_key.update_last_used()
                db.flush()

                log.info(
                    f"Successful authentication for Discord user {api_key.discord_id}"
                )
                return api_key

        log.warning("Failed authentication attempt with invalid key")
        return None

    except SQLAlchemyError as e:
        log.error(f"Database error during key authentication: {e}")
        return None

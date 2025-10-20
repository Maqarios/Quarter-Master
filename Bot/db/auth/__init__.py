# Bot/db/auth/__init__.py
"""Authentication package for the Quarter Master Bot."""

from .key_manager import (
    authenticate_key,
    create_api_key,
    generate_api_key,
    revoke_api_key,
)

__all__ = [
    "generate_api_key",
    "create_api_key",
    "authenticate_key",
    "revoke_api_key",
]

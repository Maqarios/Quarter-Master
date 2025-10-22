# Bot/config/settings.py
"""
Centralized configuration management for Quarter Master Bot.

This module provides a single source of truth for all environment variables
and configuration settings used throughout the application.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings are validated on startup and provide type safety
    throughout the application.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars
    )

    # Environment
    environment: Literal["development", "production"] = Field(
        default="development", description="Application environment"
    )

    # Logging
    logging_config: Path = Field(
        default=Path("config/logging.yaml"),
        description="Path to logging configuration file",
    )

    # Discord
    discord_token: str = Field(
        ...,  # Required field
        description="Discord bot authentication token",
        min_length=50,  # Discord tokens are typically 59+ chars
    )

    # Database
    db_host: str = Field(default="db", description="Database host")
    db_port: int = Field(default=5432, ge=1, le=65535, description="Database port")
    db_name: str = Field(default="quartermaster", description="Database name")
    db_user: str = Field(default="postgres", description="Database user")
    db_password: str = Field(..., description="Database password")

    # Computed properties
    @property
    def database_url(self) -> str:
        """Build PostgreSQL connection URL from components."""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @field_validator("logging_config")
    @classmethod
    def validate_logging_config_exists(cls, v: Path) -> Path:
        """Ensure logging config file exists."""
        if not v.exists():
            raise ValueError(f"Logging config file not found: {v}")
        return v

    @field_validator("discord_token")
    @classmethod
    def validate_discord_token(cls, v: str) -> str:
        """Ensure Discord token is not a placeholder."""
        if "your_discord_token" in v.lower():
            raise ValueError("Discord token appears to be a placeholder")
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses lru_cache to ensure settings are loaded only once
    and reused throughout the application lifecycle.
    """
    # Use pydantic's model_validate to construct the Settings from environment
    # without requiring positional constructor arguments (avoids static type checker errors).
    return Settings.model_validate({})


# Convenience exports for common patterns
settings = get_settings()

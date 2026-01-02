# Bot/cogs/api_key.py
"""
API Key Management Cog for Quarter Master Bot.

This module provides Discord slash commands for API key generation and management.
It integrates with the key_manager authentication system to allow Discord users
to generate and manage their API keys directly through Discord interactions.

Key Features:
    - Slash command for API key generation (/generate_api_key)
    - Rate limiting to prevent abuse (1 key per 60 seconds per user)
    - Ephemeral responses for security (keys only visible to requester)
    - Comprehensive error handling with user-friendly messages
    - Automatic transaction management with rollback on errors
    - Detailed logging for monitoring and debugging

Commands:
    /generate_api_key: Generate a new API key with a custom description

Security Features:
    - All responses are ephemeral (private to user)
    - Rate limiting prevents spam and abuse
    - Keys are shown only once and cannot be retrieved later
    - Input validation delegated to key_manager module
    - Proper error handling prevents information leakage

Usage Example:
    User runs: /generate_api_key description:"My production API key"
    Bot responds with the generated key, ID, and usage instructions

Error Handling:
    - ValueError: Invalid input (description length, format, etc.)
    - SQLAlchemyError: Database connection or query failures
    - CommandOnCooldown: Rate limit exceeded
    - Generic Exception: Unexpected errors with full traceback logging

Author: Quarter Master Bot Development Team
Version: 1.0.0
Dependencies: discord.py, sqlalchemy, db.auth.key_manager
"""
import logging
from typing import TYPE_CHECKING

from db import get_db_context
from db.auth import create_api_key
from discord import Interaction, app_commands
from discord.ext import commands
from sqlalchemy.exc import SQLAlchemyError

log = logging.getLogger(__name__)

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from bot import Bot


class APIKeyCog(commands.Cog):
    """
    Cog for managing API keys via Discord commands.

    Provides Discord slash commands for generating and managing API keys
    that are used to authenticate with the Quarter Master API. Implements
    security features including rate limiting and ephemeral responses.

    Attributes:
        bot (Bot): The Discord bot instance that this cog is attached to.
    """

    def __init__(self, bot: "Bot") -> None:
        """
        Initialize the APIKeyCog with a bot instance.

        Args:
            bot (Bot): The Discord bot instance that will host this cog.
        """
        self.bot = bot

    @app_commands.command(name="generate_api_key", description="Generate a new API key")
    @app_commands.describe(
        description="Description for the new API key (max 255 characters)"
    )
    @app_commands.checks.cooldown(1, 60.0)  # 1 key per 60 seconds per user
    async def generate_api_key(
        self, interaction: Interaction, description: str
    ) -> None:
        """
        Generate a new API key for the requesting user.

        Creates a new API key associated with the Discord user's ID and stores
        it in the database. The plaintext key is shown only once in the response
        and cannot be retrieved later.

        Args:
            interaction (Interaction): Discord interaction object containing user
                and command context.
            description (str): User-provided description for the key. Must be
                non-empty and no longer than 255 characters.

        Raises:
            ValueError: If description validation fails (handled internally).
            SQLAlchemyError: If database operations fail (handled internally).

        Note:
            - Keys are shown only once and cannot be retrieved later
            - Rate limited to 1 key per 60 seconds per user
            - All responses are ephemeral (visible only to the requesting user)
            - Automatic database rollback on errors
        """
        # Defer response for longer operations
        await interaction.response.defer(ephemeral=True)

        discord_id = interaction.user.id

        with get_db_context() as db:
            try:
                plaintext_key, api_key_record = create_api_key(
                    db=db, discord_id=discord_id, description=description
                )

                log.info(f"User {discord_id} generated API key {api_key_record.id}")

                await interaction.followup.send(
                    f"\n✅ **API Key Generated Successfully**\n\n"
                    f"**Description:** {api_key_record.description}\n"
                    f"**Your API Key:**\n```\n{plaintext_key}\n```\n"
                    f"⚠️ **Security Warning:**\n"
                    f"• Save this key immediately - it cannot be retrieved later\n"
                    f"• Never share this key or commit it to version control\n\n"
                    f"📝 **How to Use:**\n"
                    f"Set this as your `AGENT_API_KEY` environment variable in your `.env` file:\n"
                    f"```ini\n"
                    f"AGENT_API_KEY={plaintext_key}\n"
                    f"```\n",
                    ephemeral=True,
                )

            except ValueError as e:
                log.warning(
                    f"Validation error generating API key for user {discord_id}: {e}"
                )
                await interaction.followup.send(
                    f"❌ **Validation Error:** {str(e)}", ephemeral=True
                )

            except SQLAlchemyError as e:
                log.error(
                    f"Database error generating API key for user {discord_id}: {e}"
                )
                await interaction.followup.send(
                    "❌ **Database Error:** An error occurred while generating your API key.",
                    ephemeral=True,
                )
                raise

            except Exception as e:
                log.exception(
                    f"Unexpected error generating API key for user {discord_id}: {e}"
                )
                await interaction.followup.send(
                    "❌ **Unexpected Error:** Something went wrong.",
                    ephemeral=True,
                )
                raise

    @generate_api_key.error
    async def generate_api_key_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ) -> None:
        """
        Handle errors from the generate_api_key command.

        Specifically handles cooldown errors by informing users how long they
        must wait. Other errors are logged and a generic error message is shown.

        Args:
            interaction (Interaction): Discord interaction object for sending
                error responses.
            error (app_commands.AppCommandError): The error that occurred during
                command execution.

        Note:
            All error responses are ephemeral (visible only to the requesting user).
        """
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏳ **Rate Limit:** Please wait {error.retry_after:.0f} seconds before generating another key.",
                ephemeral=True,
            )
        else:
            log.error(f"Command error: {error}")
            await interaction.response.send_message(
                "❌ An error occurred. Please try again later.",
                ephemeral=True,
            )


async def setup(bot: "Bot") -> None:
    """Load the APIKeyCog."""
    await bot.add_cog(APIKeyCog(bot))

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
from typing import TYPE_CHECKING

from db import get_db_context
from db.auth import create_api_key
from discord import Interaction, app_commands
from discord.ext import commands
from sqlalchemy.exc import SQLAlchemyError

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from bot import Bot


class APIKeyCog(commands.Cog):
    """Cog for managing API keys via Discord commands."""

    def __init__(self, bot: "Bot") -> None:
        self.bot = bot
        self.log = bot.log.getChild(__name__)

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

        Args:
            interaction: Discord interaction object
            description: User-provided description for the key

        Note:
            Keys are shown only once and cannot be retrieved later.
            Rate limited to prevent abuse.
        """
        # Defer response for longer operations
        await interaction.response.defer(ephemeral=True)

        discord_id = interaction.user.id

        with get_db_context() as db:
            try:
                # Let create_api_key handle validation
                plaintext_key, api_key_record = create_api_key(
                    db=db, discord_id=discord_id, description=description
                )

                # Commit the transaction
                db.commit()

                self.log.info(
                    f"User {discord_id} generated API key {api_key_record.id}"
                )

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
                # Validation errors from create_api_key
                self.log.warning(
                    f"Validation error generating API key for user {discord_id}: {e}"
                )
                await interaction.followup.send(
                    f"❌ **Validation Error:** {str(e)}",
                    ephemeral=True,
                )
                db.rollback()

            except SQLAlchemyError as e:
                # Database errors
                self.log.error(
                    f"Database error generating API key for user {discord_id}: {e}"
                )
                await interaction.followup.send(
                    "❌ **Database Error:** An error occurred while generating your API key. "
                    "Please try again later or contact support.",
                    ephemeral=True,
                )
                db.rollback()

            except Exception as e:
                # Unexpected errors
                self.log.exception(
                    f"Unexpected error generating API key for user {discord_id}: {e}"
                )
                await interaction.followup.send(
                    "❌ **Unexpected Error:** Something went wrong. "
                    "Please contact support if this persists.",
                    ephemeral=True,
                )
                db.rollback()

    @generate_api_key.error
    async def generate_api_key_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ) -> None:
        """Handle cooldown and other command errors."""
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"⏳ **Rate Limit:** Please wait {error.retry_after:.0f} seconds before generating another key.",
                ephemeral=True,
            )
        else:
            self.log.error(f"Command error: {error}")
            await interaction.response.send_message(
                "❌ An error occurred. Please try again later.",
                ephemeral=True,
            )


async def setup(bot: "Bot") -> None:
    """Load the APIKeyCog."""
    await bot.add_cog(APIKeyCog(bot))

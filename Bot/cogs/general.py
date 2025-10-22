# Bot/cogs/general.py
"""General commands cog for the Discord bot.

This module provides essential utility commands that are available to all users
of the Quarter Master Discord bot. It includes basic diagnostic and informational
commands that help users and administrators verify bot functionality.

Commands:
    /ping: Check bot latency and responsiveness

Example:
    To load this cog in a bot:
        >>> await bot.load_extension('cogs.general')
"""

import logging
from typing import TYPE_CHECKING

from discord import Interaction, app_commands
from discord.ext import commands

log = logging.getLogger(__name__)

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from bot import Bot


class General(commands.Cog):
    """
    General commands cog containing basic utility and diagnostic commands.

    Provides fundamental commands useful for all Discord servers and users.
    Commands are implemented as Discord slash commands for better user
    experience and discoverability.

    Attributes:
        bot (Bot): The Discord bot instance that this cog is attached to.
    """

    def __init__(self, bot: "Bot") -> None:
        """
        Initialize the General cog with a bot instance.

        Args:
            bot (Bot): The Discord bot instance that will host this cog.
        """
        self.bot = bot

    # Slash Command: /ping
    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: Interaction) -> None:
        """
        Check the bot's latency and respond with ping time.

        Measures the WebSocket latency between the bot and Discord's servers,
        providing a quick diagnostic tool to verify bot responsiveness.

        Args:
            interaction (Interaction): The Discord interaction object containing
                command invocation context.

        Note:
            - Latency represents WebSocket heartbeat time, not command processing time
            - Response is ephemeral (private) to avoid chat clutter
            - Latency is rounded to the nearest millisecond
        """

        # Respond with latency
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(
            f"🏓 Pong! Latency: {latency}ms", ephemeral=True
        )


async def setup(bot: "Bot") -> None:
    """
    Load the General cog into the specified bot instance.

    This is the standard entry point for loading Discord.py cogs. Creates
    an instance of the General cog and adds it to the bot.

    Args:
        bot (Bot): The Discord bot instance to load this cog into.

    Raises:
        commands.ExtensionError: If the cog fails to load due to missing
            dependencies or configuration issues.
    """
    await bot.add_cog(General(bot))

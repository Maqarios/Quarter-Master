"""General commands cog for the Discord bot.

This module provides essential utility commands that are available to all users
of the Quarter Master Discord bot. It includes basic diagnostic and informational
commands that help users and administrators verify bot functionality.

The cog implements Discord slash commands using the discord.py application
commands framework, providing a modern interaction experience.

Commands:
    /ping: Check bot latency and responsiveness

Example:
    To load this cog in a bot:
        >>> await bot.load_extension('cogs.general')

    Or use the setup function directly:
        >>> from cogs.general import setup
        >>> await setup(bot)
"""

from typing import TYPE_CHECKING

from discord import Interaction, app_commands
from discord.ext import commands

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from bot import Bot


class General(commands.Cog):
    """
    General commands cog containing basic utility and diagnostic commands.

    This cog provides fundamental commands that are useful for all Discord servers
    and users. Commands are implemented as Discord slash commands for better user
    experience and discoverability.

    Attributes:
        bot (Bot): The Discord bot instance that this cog is attached to.
        log (logging.Logger): Child logger instance for this cog, derived from
            the bot's logger for consistent logging hierarchy.

    Example:
        >>> general_cog = General(bot)
        >>> await bot.add_cog(general_cog)
    """

    def __init__(self, bot: "Bot") -> None:
        """
        Initialize the General cog with bot instance and logging.

        Sets up the cog with a reference to the bot and creates a child logger
        for tracking cog-specific activities and errors.

        Args:
            bot (Bot): The Discord bot instance that will host this cog.
                Must have a 'log' attribute containing a configured logger.

        Note:
            The logger is created as a child of the bot's logger to maintain
            a consistent logging hierarchy throughout the application.
        """
        self.bot = bot
        self.log = bot.log.getChild(__name__)

    # Slash Command: /ping
    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: Interaction) -> None:
        """
        Check the bot's latency and respond with ping time.

        This command measures the WebSocket latency between the bot and Discord's
        servers, providing a quick diagnostic tool to verify bot responsiveness.
        The response is sent as an ephemeral message, visible only to the user
        who invoked the command.

        Args:
            interaction (Interaction): The Discord interaction object containing
                information about the command invocation, user, and server context.

        Response:
            Sends an ephemeral message with the current latency in milliseconds,
            formatted with a ping pong emoji for visual appeal.

        Example:
            User types: /ping
            Bot responds: "🏓 Pong! Latency: 25ms" (visible only to the user)

        Note:
            - Latency is calculated from bot.latency * 1000 and rounded to nearest ms
            - Response is ephemeral (private) to avoid chat clutter
            - Latency represents WebSocket heartbeat time, not command processing time
        """

        # Respond with latency
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(
            f"🏓 Pong! Latency: {latency}ms", ephemeral=True
        )


async def setup(bot: "Bot") -> None:
    """
    Load the General cog into the specified bot instance.

    This is the standard entry point for loading Discord.py cogs. It creates
    an instance of the General cog and adds it to the bot, making all commands
    and event handlers available.

    Args:
        bot (Bot): The Discord bot instance to load this cog into.
            Must be a running bot instance with proper Discord connection.

    Raises:
        commands.ExtensionError: If the cog fails to load due to missing
            dependencies or configuration issues.

    Example:
        Called automatically when loading the extension:
            >>> await bot.load_extension('cogs.general')

        Or called directly:
            >>> from cogs.general import setup
            >>> await setup(bot_instance)

    Note:
        This function is automatically called by Discord.py when the extension
        is loaded using bot.load_extension() or similar methods.
    """
    await bot.add_cog(General(bot))

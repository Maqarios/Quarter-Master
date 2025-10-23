# Bot/bot.py
"""Quarter Master Discord bot module.

Provides the bot implementation (``Bot``) and an asynchronous ``main()`` function
that manages lifecycle, logging, signal handling, and graceful shutdown.

The Bot class extends discord.ext.commands.Bot with enhanced functionality including:
    - Automatic cog loading and command synchronization
    - Database connectivity validation
    - Comprehensive lifecycle logging
    - Graceful shutdown and resource cleanup

Usage:
    Run via the main.py entrypoint:
        >>> python main.py

    Or import and run programmatically (useful for testing):
        >>> import asyncio
        >>> from bot import main
        >>> exit_code = asyncio.run(main())

Environment Variables:
    DISCORD_TOKEN (required): Discord bot authentication token
    LOGGING_CONFIG (optional): Path to YAML logging configuration file
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

import discord
from config import settings
from db import check_db_connection, db_engine
from discord.ext import commands, tasks

log = logging.getLogger(__name__)

# Constants
BOT_CLOSE_TIMEOUT = 10.0
TASK_CLEANUP_TIMEOUT = 5.0
DEFAULT_LOG_DIR = "/app/logs"


class Bot(commands.Bot):
    """
    Custom Discord bot class with enhanced lifecycle management.

    Extends discord.ext.commands.Bot with automatic cog loading, command tree
    synchronization, database connectivity checks, and comprehensive logging.

    Attributes:
        extension_list (list[str]): List of extension names to load on startup.
            Defaults to ["cogs.general", "cogs.api_key"].

    Example:
        >>> bot = Bot()
        >>> await bot.start(token)
    """

    def __init__(self) -> None:
        """
        Initialize the Discord bot with necessary configurations and extensions.
        This constructor sets up the bot's core functionality including:
        - Discord intents configuration to enable message content access
        - Command prefix set to "/"
        - Database health check monitoring task
        - Loading of extension modules (cogs) for general commands and API key management
        The bot inherits from discord.ext.commands.Bot and automatically starts
        the database health check task upon initialization.
        Parameters
        ----------
        None
        Returns
        -------
        None
        Attributes
        ----------
        intents : discord.Intents
            Discord intents configuration with message content enabled
        extension_list : list of str
            List of cog module paths to be loaded
        """

        # Configure Discord intents
        intents = discord.Intents.default()
        intents.message_content = True

        # Initialize the parent Bot class
        super().__init__(command_prefix="/", intents=intents)

        # Start the database health check task
        self.db_health_check.start()

        # List of extensions (cogs) to load
        self.extension_list = ["cogs.general", "cogs.api_key"]

    async def setup_hook(self) -> None:
        """
        Perform asynchronous setup tasks during bot initialization.

        Automatically called by discord.py when the bot starts. Handles:
            1. Loading all extensions from extension_list
            2. Synchronizing the command tree with Discord
            3. Validating database connection

        Note:
            - Extension loading failures are logged but don't prevent startup
            - Command tree sync failures are logged but don't prevent startup
            - Database connection failure triggers graceful shutdown
            - Bot disconnects cleanly from Discord before terminating on DB failure
        """
        # Load each extension and log the outcome
        for ext in self.extension_list:
            try:
                await self.load_extension(ext)
                log.info(f"Loaded extension: {ext}")
            except (
                commands.ExtensionNotFound,
                commands.ExtensionFailed,
                commands.ExtensionAlreadyLoaded,
            ) as e:
                log.error(f"Failed to load extension {ext}: {e}")

        # Synchronize command tree with Discord
        try:
            await self.tree.sync()
            log.info("Command tree synchronized")
        except discord.HTTPException as e:
            log.error(f"Failed to sync command tree: {e}")

        # Check database connection
        if check_db_connection():
            log.info("Database connection successful")
        else:
            log.critical("Database connection failed, shutting down bot.")
            await self.close()
            return

    async def on_ready(self) -> None:
        """
        Event handler called when the bot successfully connects to Discord.

        Logs connection confirmation and guild count information.

        Note:
            This event may be called multiple times if the bot reconnects,
            so avoid one-time initialization code here.
        """
        log.info(f"{self.user} has connected to Discord!")
        log.info(f"Bot is in {len(self.guilds)} guilds")

    @tasks.loop(minutes=10)
    async def db_health_check(self) -> None:
        """
        Perform a database health check and log critical errors if the connection fails.
        This coroutine checks the database connection status and logs a critical message
        if the connection is not healthy. It does not raise exceptions or halt execution.
        Returns:
            None
        Raises:
            None - Errors are logged but not raised
        """
        if not check_db_connection():
            log.critical("Database health check failed")

    async def close(self) -> None:
        """
        Closes the bot and cleans up resources.

        This method performs cleanup operations when shutting down the bot:
        - Disposes of the database engine to close all database connections
        - Calls the parent class's close method to properly shutdown Discord connections
        - Logs the cleanup operations for monitoring

        Returns:
            None

        Note:
            This is a coroutine and must be awaited.
        """
        # Dispose of the database engine
        db_engine.dispose()
        log.info("Database engine disposed")

        # Close the superclass resources
        await super().close()
        log.info("Discord bot instance closed")


async def run_bot() -> None:
    bot = None
    try:
        log.info("Starting Discord Bot...")
        bot = Bot()
        await bot.start(settings.discord_token)
    except asyncio.CancelledError:
        log.info("Discord Bot received cancellation signal")
        raise
    except Exception as e:
        log.error(f"Discord Bot encountered an error: {e}", exc_info=True)
        raise
    finally:
        if bot and not bot.is_closed():
            await bot.close()
        log.info("Discord Bot has shutdown")

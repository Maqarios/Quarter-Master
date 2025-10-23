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
        - Cleanup tracking to prevent duplicate resource cleanup
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
        _cleanup_done : bool
            Flag to track whether cleanup has been performed
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

        # Track if we've already cleaned up resources
        self._cleanup_done = False

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
        Gracefully shut down the bot and clean up resources.

        Performs cleanup including:
            - Disconnecting from Discord
            - Disposing of database engine connections
            - Cleaning up internal bot resources

        Note:
            - Safe to call multiple times (idempotent)
            - Database cleanup uses a flag to ensure it only runs once
            - Call this method when shutting down to ensure proper cleanup
        """
        log.info("Closing bot and cleaning up resources...")

        # Call the parent class's close method first
        await super().close()
        log.info("Discord connection closed")

        # Dispose of database engine to close all connections
        # This happens after super().close() and uses a flag to ensure
        # it only runs once even if close() is called multiple times
        if not self._cleanup_done:
            try:
                log.info("Disposing database engine...")
                db_engine.dispose()
                self._cleanup_done = True
                log.info("Database engine disposed successfully")
            except Exception as e:
                log.error(f"Error disposing database engine: {e}")
        else:
            log.debug("Cleanup already performed, skipping database disposal")

        log.info("Bot closed successfully")


async def main() -> int:
    """
    Main entry point for the Discord bot application.

    Manages the complete bot lifecycle from initialization to shutdown:
        1. Validate Discord token from settings
        2. Initialize bot instance and set up signal handlers
        3. Start bot and monitor for shutdown signals
        4. Handle graceful shutdown and cleanup on termination

    Signal Handling:
        Unix: SIGTERM, SIGINT, SIGHUP for graceful shutdown
        Windows: SIGINT for graceful shutdown

    Timeouts:
        Bot shutdown: 10 seconds maximum
        Task cleanup: 5 seconds maximum

    Returns:
        int: Exit code - 0 for success, 1 for failure.

    Raises:
        SystemExit: Not raised directly, but intended to be used with sys.exit()

    Example:
        >>> import asyncio
        >>> exit_code = asyncio.run(main())
        >>> sys.exit(exit_code)

    Note:
        Designed to be run as the main entry point with comprehensive error
        recovery and resource cleanup handling.
    """

    # Instantiate the bot
    bot = Bot()

    # Get the current event loop
    loop = asyncio.get_running_loop()

    # Create shutdown event
    shutdown_event = asyncio.Event()

    # Async signal handler
    def signal_handler(signum: int) -> None:
        log.info(
            f"Received signal {signal.Signals(signum).name} ({signum}), initiating graceful shutdown..."
        )
        shutdown_event.set()

    # Register signal handlers using the event loop (more robust than signal.signal)
    if sys.platform != "win32":  # Unix signals
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))
    else:  # Windows fallback
        signal.signal(signal.SIGINT, lambda s, f: signal_handler(s))

    # Start the bot
    bot_task: Optional[asyncio.Task] = None
    try:
        log.info("Starting bot...")
        bot_task = asyncio.create_task(bot.start(settings.discord_token))

        # Wait for either bot to finish or shutdown signal
        shutdown_task = asyncio.create_task(shutdown_event.wait())

        done, pending = await asyncio.wait(
            {bot_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED
        )

        # If shutdown was triggered, log it but don't call close() yet
        # The finally block will handle cleanup to avoid redundant calls
        if shutdown_event.is_set():
            log.info("Shutdown signal received, stopping bot task...")

        # Cancel any remaining tasks
        for task in pending:
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(asyncio.shield(task), timeout=TASK_CLEANUP_TIMEOUT)  # type: ignore
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

    except KeyboardInterrupt:
        log.info("Keyboard interrupt received, shutting down...")
    except discord.LoginFailure:
        log.error("Invalid Discord token provided")
        return 1
    except Exception as e:
        log.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    finally:
        # Final cleanup - ensure bot is closed and resources are cleaned up
        # Always attempt cleanup regardless of bot state
        try:
            log.info("Performing final bot cleanup...")
            # Call close() even if bot appears closed - our cleanup is idempotent
            await asyncio.wait_for(bot.close(), timeout=BOT_CLOSE_TIMEOUT)
        except asyncio.TimeoutError:
            log.warning("Bot close timed out, forcing shutdown")
        except Exception as e:
            log.error(f"Error during final cleanup: {e}")

        log.info("Application shutdown complete")

    return 0

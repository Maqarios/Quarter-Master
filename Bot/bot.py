# Bot/bot.py
"""
Discord bot application for Quarter Master.

This module provides a complete Discord bot implementation with features including:
- Automatic cog (extension) loading and management
- Command tree synchronization with Discord
- Database connectivity validation
- Comprehensive logging and error handling
- Graceful shutdown handling with signal management
- Cross-platform compatibility (Unix/Windows)

The bot uses SQLAlchemy for database operations and supports both development
and production environments with appropriate configurations.

Constants:
    BOT_CLOSE_TIMEOUT (float): Maximum time to wait for bot shutdown (10.0 seconds)
    TASK_CLEANUP_TIMEOUT (float): Maximum time to wait for task cleanup (5.0 seconds)
    DEFAULT_LOG_DIR (str): Default directory for log files (/app/logs)

Environment Variables:
    DISCORD_TOKEN: Required Discord bot token for authentication
    LOGGING_CONFIG: Optional path to YAML logging configuration file

Example:
    Run the bot from command line:
        $ python bot.py

    Or import and run programmatically:
        >>> import asyncio
        >>> exit_code = asyncio.run(main())
"""

import asyncio
import logging
import logging.config
import os
import signal
import sys
from typing import Optional

import discord
import yaml
from db.database import check_db_connection
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

# Constants
BOT_CLOSE_TIMEOUT = 10.0
TASK_CLEANUP_TIMEOUT = 5.0
DEFAULT_LOG_DIR = "/app/logs"


class Bot(commands.Bot):
    """
    Custom Discord bot class extending discord.ext.commands.Bot.

    This bot provides enhanced functionality including automatic cog loading,
    command tree synchronization, database connectivity checks, and comprehensive
    logging throughout its lifecycle.

    Attributes:
        log (logging.Logger): Logger instance for this bot's activities.
        extension_list (list[str]): List of extension names to load on startup.

    Example:
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> bot = Bot(logger)
        >>> # Bot is now ready to be started with bot.start(token)
    """

    def __init__(self, log: logging.Logger) -> None:
        """
        Initialize the Bot instance with logging and default configuration.

        Sets up Discord intents, command prefix, and extension list for automatic
        loading during startup.

        Args:
            log (logging.Logger): Logger instance for logging bot activities
                and errors throughout the bot's lifecycle.

        Note:
            - Message content intent is enabled for reading message content
            - Command prefix is set to "/" for slash commands
            - Extensions list includes "cogs.general" by default
        """
        # Configure Discord intents
        intents = discord.Intents.default()
        intents.message_content = True

        # Initialize the parent Bot class
        super().__init__(command_prefix="/", intents=intents)

        # Save logger
        self.log = log

        # List of extensions (cogs) to load
        self.extension_list = ["cogs.general"]

    async def setup_hook(self) -> None:
        """
        Perform asynchronous setup tasks during bot initialization.

        This method is automatically called by discord.py when the bot starts.
        It handles extension loading, command tree synchronization, and database
        connectivity validation.

        The setup process includes:
        1. Loading all extensions from extension_list
        2. Synchronizing the command tree with Discord
        3. Validating database connection

        If the database connection fails, the bot will log a critical error and
        initiate a graceful shutdown by calling close() and returning early,
        which will cause the bot task to complete and trigger the main loop's
        cleanup process.

        Note:
            - Extension loading failures are logged but don't prevent bot startup
            - Command tree sync failures are logged but don't prevent bot startup
            - Database connection failure triggers graceful shutdown without raising exceptions
            - The bot will disconnect cleanly from Discord before terminating
        """
        # Load each extension and log the outcome
        for ext in self.extension_list:
            try:
                await self.load_extension(ext)
                self.log.info(f"Loaded extension: {ext}")
            except (
                commands.ExtensionNotFound,
                commands.ExtensionFailed,
                commands.ExtensionAlreadyLoaded,
            ) as e:
                self.log.error(f"Failed to load extension {ext}: {e}")

        # Synchronize command tree with Discord
        try:
            await self.tree.sync()
            self.log.info("Command tree synchronized")
        except discord.HTTPException as e:
            self.log.error(f"Failed to sync command tree: {e}")

        # Check database connection
        if check_db_connection():
            self.log.info("Database connection successful")
        else:
            self.log.critical("Database connection failed, shutting down bot.")
            await self.close()
            return

    async def on_ready(self) -> None:
        """
        Event handler called when the bot successfully connects to Discord.

        This event is triggered after the bot has logged in and is ready to
        receive events. It logs connection confirmation and guild count.

        Note:
            This event may be called multiple times if the bot reconnects,
            so avoid putting one-time initialization code here.
        """
        self.log.info(f"{self.user} has connected to Discord!")
        self.log.info(f"Bot is in {len(self.guilds)} guilds")

    async def close(self) -> None:
        """
        Gracefully shut down the bot and clean up resources.

        Performs proper cleanup by calling the parent class's close method,
        which handles disconnecting from Discord and cleaning up internal
        resources.

        Note:
            This method should be called when shutting down the bot to ensure
            proper cleanup and avoid resource leaks.
        """
        # Call the parent class's close method
        await super().close()


async def main() -> int:
    """
    Main entry point for the Discord bot application.

    Handles the complete bot lifecycle from initialization to shutdown, including
    configuration loading, logging setup, signal handling, and graceful shutdown.

    The application flow:
    1. Load environment variables and validate Discord token
    2. Configure logging from YAML file or use basic configuration
    3. Initialize bot instance and set up signal handlers
    4. Start bot and monitor for shutdown signals
    5. Handle graceful shutdown and cleanup on termination

    Signal Handling:
        - Unix: SIGTERM, SIGINT, SIGHUP for graceful shutdown
        - Windows: SIGINT for graceful shutdown

    Timeouts:
        - Bot shutdown: 10 seconds maximum
        - Task cleanup: 5 seconds maximum

    Returns:
        int: Exit code indicating success (0) or failure (1).

    Environment Variables:
        DISCORD_TOKEN (required): Discord bot authentication token
        LOGGING_CONFIG (optional): Path to YAML logging configuration file

    Raises:
        SystemExit: For critical startup failures (invalid config, missing token)

    Example:
        >>> import asyncio
        >>> exit_code = asyncio.run(main())
        >>> print(f"Bot exited with code: {exit_code}")

    Note:
        This function is designed to be run as the main entry point and handles
        all aspects of bot lifecycle management including error recovery and
        resource cleanup.
    """

    # Load environment variables from .env file
    logging_config_path = os.getenv("LOGGING_CONFIG")
    TOKEN = os.getenv("DISCORD_TOKEN")

    # Configure logging
    if logging_config_path and os.path.exists(logging_config_path):
        try:
            with open(logging_config_path, "r") as f:
                config = yaml.safe_load(f)
                logging.config.dictConfig(config)
        except (yaml.YAMLError, OSError) as e:
            print(f"Failed to load logging config: {e}")
            sys.exit(1)
    else:
        log_dir = DEFAULT_LOG_DIR
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        logging.warning(
            f"Logging config file not found at {logging_config_path}, using basic config"
        )

    # Create a logger for this module
    log = logging.getLogger(__name__)

    # Validate the TOKEN
    if not TOKEN or not TOKEN.strip():
        log.error("DISCORD_TOKEN environment variable is not set or is empty.")
        exit(1)

    # Instantiate the bot
    bot = Bot(log)

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
        bot_task = asyncio.create_task(bot.start(TOKEN))

        # Wait for either bot to finish or shutdown signal
        shutdown_task = asyncio.create_task(shutdown_event.wait())

        done, pending = await asyncio.wait(
            {bot_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED
        )

        # If shutdown was triggered, give bot time to close gracefully
        if shutdown_event.is_set():
            log.info("Shutdown signal received, closing bot...")
            if not bot.is_closed():
                await asyncio.wait_for(bot.close(), timeout=BOT_CLOSE_TIMEOUT)

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
        # Final cleanup - ensure bot is closed
        try:
            if bot and not bot.is_closed():
                log.info("Performing final bot cleanup...")
                await asyncio.wait_for(bot.close(), timeout=BOT_CLOSE_TIMEOUT)
        except asyncio.TimeoutError:
            log.warning("Bot close timed out, forcing shutdown")
        except Exception as e:
            log.error(f"Error during final cleanup: {e}")

        log.info("Application shutdown complete")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

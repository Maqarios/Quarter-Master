"""
Discord bot application for Quarter Master.

This module initializes and runs a Discord bot with cog support,
logging configuration, and command synchronization.
"""

import asyncio
import logging
import logging.config
import os
import signal
import sys

import discord
import yaml
from discord.ext import commands


class Bot(commands.Bot):
    """
    Custom Discord bot class extending discord.ext.commands.Bot.

    This bot includes automatic cog loading, command tree synchronization,
    and comprehensive logging throughout its lifecycle.

    Attributes:
        log (logging.Logger): Logger instance for this bot.
        extension_list (list[str]): List of extension names to load on startup.
    """

    def __init__(self, log):
        """
        Initialize the Bot instance.

        Args:
            log (logging.Logger): Logger instance for logging bot activities.
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

    async def setup_hook(self):
        """
        Perform asynchronous setup tasks.

        Loads all extensions from extension_list and synchronizes
        the command tree with Discord. Called once when the bot starts.
        """
        # Load each extension and log the outcome
        for ext in self.extension_list:
            try:
                await self.load_extension(ext)
                self.log.info(f"Loaded extension: {ext}")
            except Exception as e:
                self.log.error(f"Failed to load extension {ext}: {e}")

        # Synchronize command tree with Discord
        await self.tree.sync()
        self.log.info("Command tree synchronized")

    async def on_ready(self):
        """
        Event handler called when the bot has successfully connected to Discord.

        Logs the bot's username and the number of guilds it's connected to.
        """
        self.log.info(f"{self.user} has connected to Discord!")
        self.log.info(f"Bot is in {len(self.guilds)} guilds")

    async def close(self):
        """
        Gracefully shut down the bot.

        Logs shutdown progress and calls the parent class's close method
        to properly disconnect from Discord.
        """
        # Call the parent class's close method
        await super().close()


async def main():
    """
    Main entry point for the Discord bot application.

    This coroutine handles the complete lifecycle of the bot, including:
    - Loading and validating environment variables (logging config, Discord token)
    - Configuring logging from YAML file or using basic configuration as fallback
    - Validating the Discord token
    - Instantiating and starting the bot
    - Setting up signal handlers for graceful shutdown (SIGTERM, SIGINT, SIGHUP on Unix; SIGINT on Windows)
    - Managing concurrent tasks (bot operation and shutdown event monitoring)
    - Performing graceful shutdown when signals are received
    - Cleaning up resources and closing the bot connection

    Returns:
        int: Exit code (0 for success, 1 for error)

    Raises:
        KeyboardInterrupt: Caught and handled gracefully during shutdown
        Exception: Any unexpected errors are logged and result in exit code 1

    Note:
        - Requires DISCORD_TOKEN environment variable to be set
        - Optional LOGGING_CONFIG environment variable for custom logging configuration
        - On shutdown signal, allows up to 10 seconds for bot to close gracefully
        - Pending tasks are cancelled with a 5-second timeout during cleanup
    """

    # Load environment variables from .env file
    logging_config_path = os.getenv("LOGGING_CONFIG")
    TOKEN = os.getenv("DISCORD_TOKEN")

    # Configure logging
    if logging_config_path and os.path.exists(logging_config_path):
        with open(logging_config_path, "r") as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        log_dir = "/app/logs"
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
    def signal_handler(signum):
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
    bot_task = None
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
                await asyncio.wait_for(bot.close(), timeout=10.0)

        # Cancel any remaining tasks
        for task in pending:
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(asyncio.shield(task), timeout=5.0)  # type: ignore
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass

    except KeyboardInterrupt:
        log.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        log.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    finally:
        # Final cleanup - ensure bot is closed
        try:
            if bot and not bot.is_closed():
                log.info("Performing final bot cleanup...")
                await asyncio.wait_for(bot.close(), timeout=10.0)
        except asyncio.TimeoutError:
            log.warning("Bot close timed out, forcing shutdown")
        except Exception as e:
            log.error(f"Error during final cleanup: {e}")

        log.info("Application shutdown complete")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

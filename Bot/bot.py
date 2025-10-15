"""
Discord bot application for Quarter Master.

This module initializes and runs a Discord bot with cog support,
logging configuration, and command synchronization.
"""

import logging
import logging.config
import os

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

        # Set up logging
        self.log = logging.getLogger(__name__)

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
        # Log shutdown initiation
        self.log.info("Bot is shutting down...")

        # Call the parent class's close method
        await super().close()

        # Log shutdown completion
        self.log.info("Bot has shut down successfully")


if __name__ == "__main__":
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

    # Run the bot
    try:
        bot = Bot(log)
        bot.run(TOKEN)
    except Exception as e:
        log.error(f"Error running the bot: {e}")

import logging
import logging.config
import os

import discord
import yaml
from discord.ext import commands


class Bot(commands.Bot):
    """
    A custom Discord bot class extending `commands.Bot` with logging and extension management.

    Attributes:
        log (logging.Logger): Logger instance for this bot class.
        extensions (list): List of extension module names to load.

    Methods:
        __init__():
            Initializes the bot with specific intents, logging, and extension list.

        async setup_hook():
            Loads extensions specified in `self.extensions` and logs the result.
            Synchronizes the command tree with Discord.

        async on_ready():
            Logs when the bot has connected to Discord and the number of guilds it is in.

        async close():
            Logs the shutdown process and calls the parent close method.
    """

    def __init__(self):
        """
        Initializes the bot instance with specific Discord intents, logging, and extensions.

        Sets up:
            - Discord intents with message content enabled
            - Command prefix set to "/"
            - Logger instance for the bot
            - Empty extensions list for loading cogs

        Attributes:
            log (logging.Logger): Logger instance for bot operations.
            extensions (list): Empty list to be populated with extension module names.
        """

        # Configure Discord intents
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix="/", intents=intents)

        self.log = logging.getLogger(__name__)
        self.extensions = []

    async def setup_hook(self):
        """
        Asynchronously sets up the bot by loading all extensions specified in self.extensions.
        Logs the success or failure of each extension load attempt. After loading extensions,
        synchronizes the command tree with Discord.

        Raises:
            Exception: If an extension fails to load, logs the error but continues loading others.
        """

        for ext in self.extensions:
            try:
                await self.load_extension(ext)
                self.log.info(f"Loaded extension: {ext}")
            except Exception as e:
                self.log.error(f"Failed to load extension {ext}: {e}")

        await self.tree.sync()
        self.log.info("Command tree synchronized")

    async def on_ready(self):
        """
        Event handler that is called when the bot has successfully connected to Discord.

        Logs the bot's username and the number of guilds (servers) the bot is currently in.
        """

        self.log.info(f"{self.user} has connected to Discord!")
        self.log.info(f"Bot is in {len(self.guilds)} guilds")

    async def close(self):
        """
        Asynchronously shuts down the bot, logging shutdown events before and after calling the superclass's close method.

        This method performs the following steps:
        1. Logs a message indicating the bot is shutting down.
        2. Calls the parent class's asynchronous close method to handle shutdown procedures.
        3. Logs a message confirming the bot has shut down successfully.
        """

        self.log.info("Bot is shutting down...")

        await super().close()

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

    log = logging.getLogger(__name__)

    # Validate the TOKEN
    if not TOKEN or not TOKEN.strip():
        log.error("DISCORD_TOKEN environment variable is not set or is empty.")
        exit(1)

    # Run the bot
    try:
        bot = Bot()
        bot.run(TOKEN)
    except Exception as e:
        log.error(f"Error running the bot: {e}")

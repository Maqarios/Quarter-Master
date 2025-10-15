"""General commands cog for the Discord bot.

This module contains general utility commands like ping that are available
to all users.
"""

from discord import Interaction, app_commands
from discord.ext import commands
from utils.utils import log_command


class General(commands.Cog):
    """
    General commands cog containing basic utility commands.

    Attributes:
        bot: The Discord bot instance.
        log: Logger instance for this cog.
    """

    def __init__(self, bot):
        """
        Initialize the General cog.

        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot
        self.log = bot.log.getChild(__name__)

    # Slash Command: /ping
    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: Interaction):
        """
        Check the bot's latency and respond with ping time.

        Args:
            interaction: The Discord interaction object.
        """
        # Get guild and user information
        guild = interaction.guild
        user = interaction.user

        # Log command usage with context
        log_command(self.log, "ping", guild, user)

        # Respond with latency
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(
            f"🏓 Pong! Latency: {latency}ms", ephemeral=True
        )


async def setup(bot):
    """
    Load the General cog into the bot.

    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(General(bot))

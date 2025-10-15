def log_command(log, command_name, guild, user, **kwargs):
    """
    Log command execution with standardized formatting.

    Args:
        log: Logger instance to write the log message to.
        command_name (str): Name of the command being executed.
        guild: Discord guild object where the command was invoked, or None for DMs.
        user: Discord user object who invoked the command.
        **kwargs: Additional parameters to log (e.g., command arguments).

    Example:
        >>> log_command(self.log, "ping", interaction.guild, interaction.user)
        >>> log_command(self.log, "ban", guild, user, reason="spam", duration="7d")
    """
    command_name = f"Command: {command_name}"
    user_info = (
        f"User ID: {user.id}, User Name: {user.name}, Display Name: {user.display_name}"
    )
    guild_info = f"Guild ID: {guild.id}, Guild Name: {guild.name}" if guild else "DM"
    params_info = ", ".join(f"{key}: {value}" for key, value in kwargs.items())
    params_info = params_info if params_info else None

    log.info(
        f"{command_name} | {guild_info} | {user_info}"
        + (f" | {params_info}" if params_info else "")
    )

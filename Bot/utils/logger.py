# Deprecated: Use logging configuration from config/logging.yaml instead.

import logging
import os
from logging.handlers import RotatingFileHandler


class Logger:
    """
    Logger utility class for configuring and managing application logging.

    This class sets up a logger with both console and rotating file handlers, allowing
    for centralized logging configuration across the application. It supports context
    management and can be called to retrieve the underlying logger instance.

    Args:
        name (str): Name of the logger. Defaults to "quartermaster".
        log_level (int): Logging level (e.g., logging.INFO). Defaults to logging.INFO.
        log_dir (str): Directory where log files are stored. Defaults to "/app/logs".
        max_bytes (int): Maximum size (in bytes) for a log file before rotation. Defaults to 10MB.
        backup_count (int): Number of backup log files to keep. Defaults to 5.

    Attributes:
        name (str): Logger name.
        log_level (int): Logging level.
        log_dir (str): Directory for log files.
        max_bytes (int): Maximum log file size before rotation.
        backup_count (int): Number of backup log files.
        _logger (logging.Logger): The configured logger instance.

    Methods:
        get_logger() -> logging.Logger:
            Returns the configured logger instance.

        close() -> None:
            Closes and removes all handlers from the logger.

        __repr__() -> str:
            Returns a string representation of the Logger instance.

        __str__() -> str:
            Returns a user-friendly string representation.

        __enter__():
            Enables use as a context manager.

        __exit__(exc_type, exc_val, exc_tb):
            Cleans up handlers on context exit.

        __call__() -> logging.Logger:
            Returns the logger instance when the object is called.

    Usage:
        logger = Logger().get_logger()
        logger.info("This is an info message.")

        # Or using context manager:
        with Logger() as log:
            log.get_logger().info("Logging within context.")
    """

    def __init__(
        self,
        name: str = "quartermaster",
        log_level: int = logging.INFO,
        log_dir: str = "/app/logs",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB default
        backup_count: int = 5,
    ):
        """
        Initializes the logger utility with the specified configuration.

        Args:
            name (str): The name of the logger. Defaults to "quartermaster".
            log_level (int): The logging level (e.g., logging.INFO, logging.DEBUG). Defaults to logging.INFO.
            log_dir (str): The directory where log files will be stored. Defaults to "/app/logs".
            max_bytes (int): The maximum size (in bytes) of a log file before it is rotated. Defaults to 10MB.
            backup_count (int): The number of backup log files to keep. Defaults to 5.
        """

        self.name = name
        self.log_level = log_level
        self.log_dir = log_dir
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """
        Initializes and configures a logger for the current instance.

        This method sets up a logger with the specified name and log level. It attaches a console handler and, if a log directory is provided, a rotating file handler that writes to a shared log file ("bot.log"). The logger is configured with custom formatting for both handlers. If the logger already has handlers, it is returned as-is to prevent duplicate handlers. File logging setup errors are caught and logged as warnings.

        Returns:
            logging.Logger: The configured logger instance.
        """

        logger = logging.getLogger(self.name)

        # Skip if already configured
        if logger.handlers:
            return logger

        logger.setLevel(self.log_level)
        logger.propagate = False

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(console_handler)

        # File handler - single shared file for all modules
        if self.log_dir:
            try:
                os.makedirs(self.log_dir, exist_ok=True)
                # Use a single shared log file name instead of per-module files
                log_file = os.path.join(self.log_dir, "bot.log")
                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=self.max_bytes,
                    backupCount=self.backup_count,
                    encoding="utf-8",
                )
                file_handler.setLevel(self.log_level)
                file_handler.setFormatter(
                    logging.Formatter(
                        "%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s",
                        datefmt="%Y-%m-%d %H:%M:%S",
                    )
                )
                logger.addHandler(file_handler)
            except (OSError, PermissionError) as e:
                logger.warning(f"Failed to setup file logging: {e}")

        return logger

    def get_logger(self) -> logging.Logger:
        """
        Returns the logger instance associated with this object.

        Returns:
            logging.Logger: The logger instance used for logging messages.
        """

        return self._logger

    def close(self) -> None:
        """
        Closes and removes all handlers associated with the logger.

        This method iterates over all handlers currently attached to the logger,
        closes each handler to release any resources (such as file handles or network connections),
        and then removes the handler from the logger to prevent further logging output.
        """

        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)

    def __repr__(self) -> str:
        """
        Return a string representation of the Logger instance, including its name and log level.

        Returns:
            str: A string in the format "Logger(name='<name>', level=<log_level_name>)".
        """

        return (
            f"Logger(name='{self.name}', level={logging.getLevelName(self.log_level)})"
        )

    def __str__(self) -> str:
        """
        Return a string representation of the Logger instance, including its name.
        Returns:
            str: A formatted string in the form 'Logger[<name>]'.
        """

        return f"Logger[{self.name}]"

    def __enter__(self):
        """
        Enters the runtime context related to this object.

        Returns:
            self: Returns the context manager instance itself.
        """

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Handles cleanup actions when exiting the context manager.

        Args:
            exc_type (Type[BaseException] or None): The exception type, if an exception was raised, otherwise None.
            exc_val (BaseException or None): The exception instance, if an exception was raised, otherwise None.
            exc_tb (TracebackType or None): The traceback object, if an exception was raised, otherwise None.

        Returns:
            bool: False to indicate that any exception should be propagated.

        This method ensures that resources are properly closed when exiting the context, and does not suppress exceptions.
        """

        self.close()
        return False

    def __call__(self) -> logging.Logger:
        """
        Allows the instance to be called as a function, returning the underlying logger.

        Returns:
            logging.Logger: The logger instance associated with this object.
        """

        return self._logger

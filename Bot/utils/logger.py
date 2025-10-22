"""Logging utilities for Quarter Master Bot.

This module provides centralized logging configuration management with support for
YAML-based configuration files and sensible defaults when no configuration is found.

The setup_logging function handles:
    - Loading logging configuration from YAML files
    - Setting up default logging with appropriate formatting
    - Creating log directories as needed
    - Comprehensive error handling for configuration failures

Example:
    Basic usage with defaults:
        >>> from utils.logger import setup_logging
        >>> setup_logging()

    Custom log level and directory:
        >>> setup_logging(level=logging.DEBUG, log_dir="/custom/logs")

Configuration:
    If settings.logging_config points to a valid YAML file, that configuration
    will be used. Otherwise, a basic console logger is configured with the
    specified level and format.
"""

import logging.config
import os

import yaml
from config import settings


def setup_logging(
    level: int = logging.INFO,
    log_dir: str = "/app/logs",
) -> None:
    """
    Configure application logging from YAML config or use basic defaults.

    Attempts to load logging configuration from the path specified in
    settings.logging_config. If the file doesn't exist or cannot be loaded,
    falls back to a basic logging configuration with console output.

    Args:
        level (int): Default logging level to use when YAML config is not
            available. Defaults to logging.INFO.
        log_dir (str): Directory to create for log files when using basic
            configuration. Defaults to "/app/logs". Created if it doesn't exist.

    Raises:
        RuntimeError: If the YAML config file exists but cannot be loaded due to
            parsing errors, I/O errors, or invalid configuration (e.g., missing
            formatter classes).

    Note:
        - When using YAML config, all settings come from the config file
        - When using basic config, the level and log_dir parameters are used
        - Log directory is created automatically when using basic configuration
    """
    if settings.logging_config.exists():
        try:
            with open(settings.logging_config, "r") as f:
                config = yaml.safe_load(f)
                logging.config.dictConfig(config)
        except (yaml.YAMLError, OSError) as e:
            raise RuntimeError(
                f"Failed to load logging config from {settings.logging_config}: {e}"
            )
        except ValueError as e:
            # This catches formatter class not found errors
            raise RuntimeError(f"Invalid logging config (missing dependency?): {e}")
    else:
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            level=level,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

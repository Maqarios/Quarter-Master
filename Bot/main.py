#!/usr/bin/env python3
# Bot/main.py
"""Command-line entrypoint for the Quarter Master application.

This module runs the Discord bot's ``main()`` coroutine and exits with its
return code. Orchestration (how processes are started) is kept separate from
application logic (in ``bot.py``).

Usage:
    Run directly:
        >>> python main.py

    Or make it executable on Unix:
        >>> chmod +x main.py
        >>> ./main.py

Note:
    For testing or embedding the bot in other applications, import ``bot.main``
    directly instead of invoking this script.
"""

import asyncio
import sys

from bot import main as run_bot
from utils import setup_logging

if __name__ == "__main__":
    # Execute the bot's main function and exit with its return code.
    # This ensures proper cleanup and allows the exit code to be propagated
    # to the operating system for monitoring and orchestration tools.
    setup_logging()

    exit_code = asyncio.run(run_bot())
    sys.exit(exit_code)

#!/usr/bin/env python3
# Bot/main.py
"""
Main entry point for Quarter Master application.

This module serves as the primary entry point for running the Quarter Master
Discord bot. It imports and executes the bot's main function, handling the
application lifecycle and exit codes.

This separation allows the bot module to be imported and tested independently
while maintaining a clean entry point for production deployment.

Usage:
    Run from command line:
        $ python main.py

    Or make executable and run directly (Unix):
        $ chmod +x main.py
        $ ./main.py

Exit Codes:
    0: Successful execution and graceful shutdown
    1: Error during execution (invalid token, configuration error, etc.)

Example:
    >>> import subprocess
    >>> result = subprocess.run(['python', 'main.py'])
    >>> print(f"Bot exited with code: {result.returncode}")
"""

import asyncio
import sys

from bot import main as run_bot

if __name__ == "__main__":
    """
    Execute the bot's main function and exit with its return code.

    This ensures proper cleanup and allows the exit code to be propagated
    to the operating system for monitoring and orchestration tools.
    """
    exit_code = asyncio.run(run_bot())
    sys.exit(exit_code)

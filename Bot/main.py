#!/usr/bin/env python3
# Bot/main.py
"""Command-line entrypoint for the Quarter Master application.

This small module runs the Discord bot's ``main()`` coroutine and exits
with its return code. Keep orchestration (how processes are started)
separate from application logic (in ``bot.py``).

Run:
    python main.py

Or make it executable on Unix:
    chmod +x main.py
    ./main.py

Notes:
    - For testing or embedding, import ``bot.main`` directly instead of
      invoking this script.
    - In future you can extend this entrypoint to launch multiple
      services (for example, an API server) concurrently.
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

#!/usr/bin/env python3
# Bot/main.py
"""Command-line entrypoint for the Quarter Master application."""

import asyncio
import logging
import signal
import sys

from api_server import run_api
from bot import run_bot
from utils import setup_logging

setup_logging()
log = logging.getLogger(__name__)


async def main() -> int:
    """Run the main application with proper shutdown handling."""
    shutdown_event = asyncio.Event()

    def signal_handler(sig):
        log.info(f"Received signal {sig}, initiating shutdown...")
        shutdown_event.set()

    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))

    try:
        log.info("Starting bot and API server...")
        bot_task = asyncio.create_task(run_bot())
        api_task = asyncio.create_task(run_api())

        # Wait for shutdown signal OR task completion
        shutdown_task = asyncio.create_task(shutdown_event.wait())
        done, pending = await asyncio.wait(
            {bot_task, api_task, shutdown_task}, return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel all pending tasks
        for task in pending:
            task.cancel()

        # Wait for cancellations with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*pending, return_exceptions=True), timeout=10.0  # type: ignore
            )
        except asyncio.TimeoutError:
            log.warning("Some tasks did not cancel gracefully")

        # Check for exceptions
        for task in done:
            if task != shutdown_task and task.exception():
                log.error(f"Task failed: {task.exception()}")
                return 1

        return 0

    except Exception as e:
        log.error(f"Entrypoint encountered an error: {e}", exc_info=True)
        return 1
    finally:
        log.info("Entrypoint has shutdown.")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

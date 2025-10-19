"""
Main entry point for the Minecraft Wiki Bot
"""

import argparse
import logging

import uvicorn

from ..core.config import settings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minecraft Wiki Bot")
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging (shows full messages and responses)",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging level"
    )

    args = parser.parse_args()

    # Set verbosity based on command line args
    if args.verbose:
        settings.verbose_logging = True
        print("🔊 Verbose logging enabled")

    # Set log level
    if args.debug:
        settings.log_level = "DEBUG"
        print("🐛 Debug logging enabled")

    # Configure logging
    logging.basicConfig(level=getattr(logging, settings.log_level))

    uvicorn.run("src.bot.api:app", host="0.0.0.0", port=settings.bot_port, reload=False)

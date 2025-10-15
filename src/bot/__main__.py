"""
Main entry point for the Minecraft Wiki Bot
"""

import uvicorn
from .config import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.bot.api:app",
        host="0.0.0.0",
        port=settings.bot_port,
        reload=False
    )
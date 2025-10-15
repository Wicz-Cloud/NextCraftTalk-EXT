"""
Message processing utilities for the Minecraft bot
"""

import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


def should_respond(message: str, actor_id: str) -> bool:
    """
    Determine if bot should respond to this message

    Args:
        message: The message text
        actor_id: ID of the message sender

    Returns:
        bool: True if bot should respond
    """
    # Don't respond to own messages
    if actor_id == settings.bot_name.lower():
        return False

    # Respond if mentioned
    if f"@{settings.bot_name.lower()}" in message.lower():
        return True

    # Respond to questions about Minecraft
    minecraft_keywords = [
        "craft",
        "recipe",
        "how do i",
        "how to make",
        "minecraft",
        "brewing",
        "enchant",
        "smelt",
        "pickaxe",
        "sword",
        "armor",
        "potion",
    ]

    message_lower = message.lower()
    return any(keyword in message_lower for keyword in minecraft_keywords)


def clean_message(message: str) -> str:
    """
    Clean and prepare message for processing

    Args:
        message: Raw message text

    Returns:
        str: Cleaned message
    """
    # Remove bot mentions
    message = message.replace(f"@{settings.bot_name}", "").strip()
    message = message.replace(f"@{settings.bot_name.lower()}", "").strip()

    # Remove common prefixes
    prefixes_to_remove = ["hey", "hi", "hello", "bot"]
    message_lower = message.lower()
    for prefix in prefixes_to_remove:
        if message_lower.startswith(prefix + " "):
            message = message[len(prefix) + 1 :].strip()
            break

    return message

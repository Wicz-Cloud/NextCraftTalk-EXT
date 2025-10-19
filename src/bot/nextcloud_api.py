"""
Nextcloud Talk API client for the Minecraft bot
"""

import asyncio
import logging

import requests

from ..core.config import settings

logger = logging.getLogger(__name__)


def send_thinking_message(token: str) -> int | None:
    """
    Send thinking message and return its ID

    Args:
        token: Conversation token

    Returns:
        Optional[int]: Message ID if successful, None otherwise
    """
    base_url = f"{settings.nextcloud_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"

    headers = {
        "OCS-APIRequest": "true",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.nextcloud_bot_token}",
    }

    data = {"message": "🤔 Thinking...", "replyTo": 0}

    try:
        response = requests.post(base_url, headers=headers, json=data, timeout=10)
        if settings.verbose_logging:
            logger.info(
                f"Thinking message POST status: {response.status_code}, "
                f"text: {response.text[:200]}"
            )
        if response.status_code == 201:
            response_data = response.json()
            message_id = response_data.get("ocs", {}).get("data", {}).get("id")
            if settings.verbose_logging:
                logger.info(f"✓ Thinking message sent, ID: {message_id}")
            return int(message_id) if message_id is not None else None
        else:
            logger.error(
                f"Failed to send thinking message: {response.status_code} - "
                f"{response.text}"
            )
            return None
    except Exception as e:
        logger.error(f"Error sending thinking message: {e}")
        return None


async def send_to_nextcloud_fallback(token: str, message: str) -> bool:
    """
    Fallback: send new message if editing fails

    Args:
        token: Conversation token
        message: Message to send

    Returns:
        bool: True if successful
    """
    base_url = f"{settings.nextcloud_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"

    headers = {
        "OCS-APIRequest": "true",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.nextcloud_bot_token}",
    }

    data = {"message": message, "replyTo": 0}

    def _send() -> bool:
        try:
            response = requests.post(base_url, headers=headers, json=data, timeout=10)
            if response.status_code == 201:
                if settings.verbose_logging:
                    logger.info(f"✓ Fallback message sent to conversation {token}")
                return True
            else:
                logger.error(f"Failed to send fallback message: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error sending fallback message: {e}")
            return False

    return await asyncio.to_thread(_send)


async def edit_message(token: str, message_id: int, new_message: str) -> bool:
    """
    Edit a message in Nextcloud Talk

    Args:
        token: Conversation token
        message_id: ID of message to edit
        new_message: New message content

    Returns:
        bool: True if successful
    """
    base_url = f"{settings.nextcloud_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
    edit_url = f"{base_url}/{message_id}"

    headers = {
        "OCS-APIRequest": "true",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.nextcloud_bot_token}",
    }

    data = {"message": new_message}

    def _edit() -> bool:
        try:
            response = requests.put(edit_url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                if settings.verbose_logging:
                    logger.info(f"✓ Message updated in conversation {token}")
                return True
            else:
                logger.error(
                    f"Failed to edit message: {response.status_code} - {response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            return False

    return await asyncio.to_thread(_edit)


async def delete_message(token: str, message_id: int) -> bool:
    """
    Delete a message in Nextcloud Talk

    Args:
        token: Conversation token
        message_id: ID of message to delete

    Returns:
        bool: True if successful
    """
    base_url = f"{settings.nextcloud_url}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
    delete_url = f"{base_url}/{message_id}"

    headers = {
        "OCS-APIRequest": "true",
        "Authorization": f"Bearer {settings.nextcloud_bot_token}",
    }

    def _delete() -> bool:
        try:
            response = requests.delete(delete_url, headers=headers, timeout=10)
            if response.status_code == 200:
                if settings.verbose_logging:
                    logger.info(f"✓ Message deleted in conversation {token}")
                return True
            else:
                logger.error(
                    f"Failed to delete message: {response.status_code} - "
                    f"{response.text}"
                )
                return False
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return False

    return await asyncio.to_thread(_delete)


def format_answer_markdown(result: dict) -> str:
    """
    Format x.ai result as markdown for Nextcloud

    Args:
        result: x.ai pipeline result dictionary

    Returns:
        str: Formatted markdown message
    """
    answer = str(result["answer"])

    # Add sources if available
    # if result.get('sources'):
    #     answer += "\n\n📚 **Sources:**"
    #     for source in result['sources'][:3]:
    #     answer += f"\n• [{source['title']}]({source['url']})"

    return answer

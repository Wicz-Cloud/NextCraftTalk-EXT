"""
Security utilities for webhook signature verification
"""

import hashlib
import hmac
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


def verify_signature(
    raw_body: bytes, signature_header: str, random_header: str
) -> bool:
    """
    Verify Nextcloud Talk webhook signature

    Per Nextcloud Talk docs: Create HMAC with SHA256 over the RANDOM header
    and the request body using the shared secret.

    Args:
        raw_body: Raw request body bytes
        signature_header: X-Nextcloud-Talk-Signature header value
        random_header: X-Nextcloud-Talk-Random header value

    Returns:
        bool: True if signature is valid
    """
    if not signature_header:
        logger.warning("No signature header provided - accepting for local development")
        return True  # Allow unsigned for local testing

    if not settings.shared_secret:
        logger.warning("No SHARED_SECRET configured - accepting unsigned requests")
        return True

    try:
        # Nextcloud Talk signs: RANDOM_HEADER + REQUEST_BODY
        message_to_sign = random_header.encode("utf-8") + raw_body

        # Create HMAC-SHA256 signature
        expected_signature = hmac.new(
            settings.shared_secret.encode("utf-8"), message_to_sign, hashlib.sha256
        ).hexdigest()

        provided_signature = signature_header.lower().strip()

        # Only log detailed security debug info when in DEBUG mode
        if settings.log_level.upper() == "DEBUG":
            logger.info(f"DEBUG: Random header: {random_header}")
            logger.info(f"DEBUG: Expected signature: {expected_signature[:16]}...")
            logger.info(f"DEBUG: Received signature: {provided_signature[:16]}...")

        if hmac.compare_digest(provided_signature, expected_signature.lower()):
            if settings.verbose_logging:
                logger.info("✓ Webhook signature verified")
            return True
        else:
            logger.warning("Invalid webhook signature")
            return False

    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False

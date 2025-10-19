"""
FastAPI application for Minecraft Wiki Bot
"""

import asyncio
import json
import logging

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from pydantic import BaseModel

from ..core.config import settings
from ..xai.pipeline import DirectXAIPipeline
from .message import clean_message
from .nextcloud_api import (
    delete_message,
    send_thinking_message,
    send_to_nextcloud_fallback,
)
from .security import verify_signature

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Add file logging
settings.ensure_log_directory()
file_handler = logging.FileHandler(settings.log_path)
file_handler.setLevel(getattr(logging, settings.log_level))
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Initialize FastAPI
app = FastAPI(title="Minecraft Wiki Bot for Nextcloud Talk")

# Initialize components
xai_pipeline = None


class NextcloudMessage(BaseModel):
    """Nextcloud Talk webhook message format"""

    object: str  # "message"
    actor_id: str
    actor_displayname: str
    message: str
    token: str
    conversation_name: str | None = None

    # Optional fields
    timestamp: int | None = None
    message_id: int | None = None


@app.on_event("startup")  # type: ignore
async def startup_event() -> None:
    """Initialize x.ai pipeline on startup


    Loads x.ai pipeline with file watching and tests connection.
    Dependencies:
    - Application logs in logs/ directory
    - prompt_template.txt file (mounted via docker volume)
    """
    global xai_pipeline

    logger.info("🚀 Starting Minecraft Wiki Bot...")

    try:
        # Initialize direct x.ai pipeline
        logger.info("Initializing direct x.ai pipeline...")
        xai_pipeline = DirectXAIPipeline(
            xai_api_key=settings.xai_api_key,  # From XAI_API_KEY in .env
            xai_url=settings.xai_url,  # x.ai API URL
            model_name=settings.model_name,  # From MODEL_NAME in .env
            prompt_template_path=settings.prompt_template_path,
            # From PROMPT_TEMPLATE_PATH
        )

        logger.info("✓ Bot ready!")

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise


@app.on_event("shutdown")  # type: ignore
async def shutdown_event() -> None:
    """Cleanup on shutdown

    Stops file watcher and cleans up resources.
    """
    global xai_pipeline
    if xai_pipeline:
        xai_pipeline.stop_file_watcher()
    logger.info("Bot shutdown complete")


@app.get("/")  # type: ignore
async def root() -> dict:
    """Health check endpoint"""
    return {
        "status": "running",
        "bot_name": settings.bot_name,
        "service": "Minecraft Wiki Bot for Nextcloud Talk",
    }


@app.get("/health")  # type: ignore
async def health() -> dict:
    """Detailed health check endpoint"""
    # Check if we have the required settings for x.ai
    has_xai_config = bool(
        settings.xai_api_key and settings.xai_api_key != "your-xai-api-key-here"
    )

    health_status = {
        "status": "healthy" if has_xai_config else "unhealthy",
        "components": {
            "xai_pipeline": has_xai_config,  # Check if x.ai is configured
        },
        "bot_name": settings.bot_name,
    }

    return health_status


@app.get("/health")  # type: ignore
async def health_check() -> dict:
    """Detailed health check"""
    # Check if we have the required settings for x.ai
    has_xai_config = bool(
        settings.xai_api_key and settings.xai_api_key != "your-xai-api-key-here"
    )

    health = {
        "status": "healthy" if has_xai_config else "unhealthy",
        "components": {
            "xai_pipeline": has_xai_config,  # Check if x.ai is configured
        },
        "bot_name": settings.bot_name,
    }

    return health


async def process_and_respond(
    token: str, query: str, thinking_message_id: int | None
) -> None:
    """
    Process the query and send response, then delete thinking message

    Args:
        token: Conversation token
        query: User query
        thinking_message_id: ID of thinking message to delete
    """
    try:
        # Generate response
        if xai_pipeline is None:
            response = "Bot is not initialized yet."
        else:
            result = xai_pipeline.answer_question(query)
            response = (
                str(result["answer"])
                if result and "answer" in result
                else "I couldn't generate a response."
            )

        # Send the answer as a new message
        await send_to_nextcloud_fallback(token, response)

        # Delete the thinking message
        if thinking_message_id is not None:
            await delete_message(token, thinking_message_id)

    except Exception as e:
        logger.error(f"Error in process_and_respond: {e}")
        # Send error message
        await send_to_nextcloud_fallback(
            token, "Sorry, I had trouble answering that. Try again!"
        )


@app.post("/webhook")  # type: ignore
async def webhook_handler(request: Request, background_tasks: BackgroundTasks) -> dict:
    """
    Handle incoming webhooks from Nextcloud Talk
    """
    if settings.verbose_logging:
        logger.info("Webhook endpoint hit!")

    try:
        # Get raw request body for signature verification
        raw_body = await request.body()

        # Verify webhook signature
        signature_header = request.headers.get("X-Nextcloud-Talk-Signature")
        random_header = request.headers.get("X-Nextcloud-Talk-Random", "")
        if not verify_signature(raw_body, signature_header or "", random_header):
            logger.warning("Invalid webhook signature - rejecting request")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse webhook data
        data = json.loads(raw_body.decode("utf-8"))
        if settings.verbose_logging:
            logger.info(f"Received webhook: {data}")
        else:
            logger.debug(f"Received webhook: {data}")
            logger.info("Received webhook from Nextcloud Talk")

        # Parse ActivityPub webhook format from Nextcloud Talk
        if "object" in data and "content" in data["object"]:
            # New ActivityPub format
            content_str = data["object"]["content"]
            content_data = json.loads(content_str)
            message = content_data.get("message", "")
            token = data["target"]["id"]  # Conversation token
            actor_name = data["actor"].get("name", "User")
            actor_id = data["actor"].get("id", "")
        else:
            # Legacy format (fallback)
            if "message" not in data or "token" not in data:
                raise HTTPException(status_code=400, detail="Missing required fields")
            message = data["message"]
            token = data["token"]
            actor_id = data.get("actor_id", "")
            actor_name = data.get("actor_displayname", "User")

        # Ignore messages from the bot itself to prevent infinite loops
        if actor_id.endswith("Minecraft Bot") or actor_name in [
            "Mincrafter",
            "minecraft_bot",
        ]:
            if settings.verbose_logging:
                logger.info(
                    f"Ignoring message from bot itself: {actor_name} ({actor_id})"
                )
            return {"status": "ignored - bot message"}

        # Check if we should respond
        # if not should_respond(message, actor_id):
        #     logger.info("Ignoring message (not relevant)")
        #     return {"status": "ignored"}

        # Clean message
        query = clean_message(message)
        if settings.verbose_logging:
            logger.info(f"Processing query: {query}")

        # Send thinking message immediately
        thinking_message_id = send_thinking_message(token)

        # Process in background
        asyncio.create_task(process_and_respond(token, query, thinking_message_id))
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/test-query")  # type: ignore
async def test_query(query: str) -> dict:
    """Test endpoint for debugging (no Nextcloud required)"""
    if settings.verbose_logging:
        logger.info(f"Test query: {query}")

    # Query x.ai pipeline
    if xai_pipeline is None:
        result = {"answer": "Bot is not initialized yet."}
    else:
        result = xai_pipeline.answer_question(query)
        if result and "answer" in result:
            result = result
        else:
            result = {"answer": "No result"}

    return {"result": result, "source": "xai"}


@app.get("/stats")  # type: ignore
async def get_stats() -> dict:
    """Get bot statistics"""
    stats = {}

    # No vector database stats in x.ai-only architecture
    stats["architecture"] = "x.ai direct integration"

    return stats


@app.post("/reload-prompt")  # type: ignore
async def reload_prompt() -> dict:
    """Manually reload the prompt template

    Forces reload of prompt_template.txt without file watcher.
    Useful if file watching fails or for immediate reload.
    Dependencies: x.ai pipeline must be initialized.
    """
    if not xai_pipeline:
        raise HTTPException(status_code=503, detail="x.ai pipeline not initialized")

    try:
        xai_pipeline.reload_prompt_template()
        return {"status": "success", "message": "Prompt template reloaded"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to reload prompt: {str(e)}"
        ) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=settings.bot_port)

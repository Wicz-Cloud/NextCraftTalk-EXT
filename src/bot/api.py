"""
FastAPI application for Minecraft Wiki Bot
"""

import asyncio
import json
import logging
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict

from ..core.config import settings
from .security import verify_signature
from .message import should_respond, clean_message
from .nextcloud_api import (
    send_thinking_message,
    send_to_nextcloud_fallback,
    delete_message,
    format_answer_markdown
)
from ..data.vector_db import MinecraftVectorDB
from ..rag.pipeline import MinecraftRAGPipeline

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Add file logging
settings.ensure_log_directory()
file_handler = logging.FileHandler(settings.log_path)
file_handler.setLevel(getattr(logging, settings.log_level))
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Initialize FastAPI
app = FastAPI(title="Minecraft Wiki Bot for Nextcloud Talk")

# Initialize components
vector_db = None
rag_pipeline = None


class NextcloudMessage(BaseModel):
    """Nextcloud Talk webhook message format"""
    object: str  # "message"
    actor_id: str
    actor_displayname: str
    message: str
    token: str
    conversation_name: Optional[str] = None

    # Optional fields
    timestamp: Optional[int] = None
    message_id: Optional[int] = None


@app.on_event("startup")
async def startup_event():
    """Initialize RAG components on startup"""
    global vector_db, rag_pipeline

    logger.info("🚀 Starting Minecraft Wiki Bot...")

    try:
        # Initialize vector database
        logger.info("Loading vector database...")
        vector_db = MinecraftVectorDB()

        # Initialize RAG pipeline
        logger.info("Initializing RAG pipeline...")
        rag_pipeline = MinecraftRAGPipeline(
            vector_db=vector_db,
            ollama_url=settings.ollama_url,
            model_name=settings.model_name
        )

        logger.info("✓ Bot ready!")

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Bot shutdown complete")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "bot_name": settings.bot_name,
        "service": "Minecraft Wiki Bot for Nextcloud Talk"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    health = {
        "status": "healthy",
        "components": {
            "vector_db": vector_db is not None,
            "rag_pipeline": rag_pipeline is not None
        }
    }

    return health


async def process_and_respond(token: str, query: str, thinking_message_id: int):
    """
    Process the query and send response, then delete thinking message

    Args:
        token: Conversation token
        query: User query
        thinking_message_id: ID of thinking message to delete
    """
    try:
        # Generate response
        response = rag_pipeline.answer_question(query)['answer']

        # Send the answer as a new message
        await send_to_nextcloud_fallback(token, response)

        # Delete the thinking message
        await delete_message(token, thinking_message_id)

    except Exception as e:
        logger.error(f"Error in process_and_respond: {e}")
        # Send error message
        await send_to_nextcloud_fallback(token, "Sorry, I had trouble answering that. Try again!")


@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """
    Handle incoming webhooks from Nextcloud Talk
    """
    logger.info("Webhook endpoint hit!")
    try:
        # Get raw request body for signature verification
        raw_body = await request.body()

        # Verify webhook signature
        signature_header = request.headers.get('X-Nextcloud-Talk-Signature')
        random_header = request.headers.get('X-Nextcloud-Talk-Random', '')
        if not verify_signature(raw_body, signature_header, random_header):
            logger.warning("Invalid webhook signature - rejecting request")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse webhook data
        data = json.loads(raw_body.decode('utf-8'))
        logger.info(f"Received webhook: {data}")

        # Parse ActivityPub webhook format from Nextcloud Talk
        if 'object' in data and 'content' in data['object']:
            # New ActivityPub format
            content_str = data['object']['content']
            content_data = json.loads(content_str)
            message = content_data.get('message', '')
            token = data['target']['id']  # Conversation token
            actor_name = data['actor'].get('name', 'User')
            actor_id = data['actor'].get('id', '')
        else:
            # Legacy format (fallback)
            if 'message' not in data or 'token' not in data:
                raise HTTPException(status_code=400, detail="Missing required fields")
            message = data['message']
            token = data['token']
            actor_id = data.get('actor_id', '')
            actor_name = data.get('actor_displayname', 'User')

        # Ignore messages from the bot itself to prevent infinite loops
        if actor_id.endswith('Minecraft Bot') or actor_name in ['Mincrafter', 'minecraft_bot']:
            logger.info(f"Ignoring message from bot itself: {actor_name} ({actor_id})")
            return {"status": "ignored - bot message"}

        # Check if we should respond
        # if not should_respond(message, actor_id):
        #     logger.info("Ignoring message (not relevant)")
        #     return {"status": "ignored"}

        # Clean message
        query = clean_message(message)
        logger.info(f"Processing query: {query}")

        # Send thinking message immediately
        thinking_message_id = send_thinking_message(token)

        # Process in background
        asyncio.create_task(process_and_respond(token, query, thinking_message_id))
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test-query")
async def test_query(query: str):
    """Test endpoint for debugging (no Nextcloud required)"""
    logger.info(f"Test query: {query}")

    # Query RAG
    result = rag_pipeline.answer_question(query)

    return {"result": result, "source": "rag"}


@app.get("/stats")
async def get_stats():
    """Get bot statistics"""
    stats = {}

    if vector_db:
        stats["vector_db_stats"] = vector_db.get_collection_stats()

    return stats


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.bot_port)
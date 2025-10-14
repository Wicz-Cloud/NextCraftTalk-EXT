"""
Nextcloud Talk Bot - FastAPI Service
Handles webhooks from Nextcloud Talk and responds with Minecraft answers
"""

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict
import requests
import os
from dotenv import load_dotenv
import logging
from pathlib import Path
import hmac
import hashlib
import json

from vector_db import MinecraftVectorDB
from rag_pipeline import MinecraftRAGPipeline
from cache_manager import RecipeCache

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add file logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
file_handler = logging.FileHandler(log_dir / "nextcloud_bot.log")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Initialize FastAPI
app = FastAPI(title="Minecraft Wiki Bot for Nextcloud Talk")

# Configuration
NEXTCLOUD_URL = os.getenv("NEXTCLOUD_URL", "https://your-nextcloud.com")
NEXTCLOUD_TOKEN = os.getenv("NEXTCLOUD_BOT_TOKEN", "")
SHARED_SECRET = os.getenv("SHARED_SECRET", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL_NAME = os.getenv("MODEL_NAME", "phi3:mini")
BOT_NAME = os.getenv("BOT_NAME", "MinecraftBot")

# Initialize components
vector_db = None
rag_pipeline = None
cache = None


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
    global vector_db, rag_pipeline, cache
    
    logger.info("🚀 Starting Minecraft Wiki Bot...")
    
    try:
        # Initialize vector database
        logger.info("Loading vector database...")
        vector_db = MinecraftVectorDB()
        
        # Initialize RAG pipeline
        logger.info("Initializing RAG pipeline...")
        rag_pipeline = MinecraftRAGPipeline(
            vector_db=vector_db,
            ollama_url=OLLAMA_URL,
            model_name=MODEL_NAME
        )
        
        # Initialize cache
        logger.info("Loading cache...")
        cache = RecipeCache()
        
        logger.info("✓ Bot ready!")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if cache:
        cache.close()
    logger.info("Bot shutdown complete")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "bot_name": BOT_NAME,
        "service": "Minecraft Wiki Bot for Nextcloud Talk"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    health = {
        "status": "healthy",
        "components": {
            "vector_db": vector_db is not None,
            "rag_pipeline": rag_pipeline is not None,
            "cache": cache is not None
        }
    }
    
    if cache:
        health["cache_stats"] = cache.get_cache_stats()
    
    return health


def should_respond(message: str, actor_id: str) -> bool:
    """Determine if bot should respond to this message"""
    # Don't respond to own messages
    if actor_id == BOT_NAME.lower():
        return False
    
    # Respond if mentioned
    if f"@{BOT_NAME.lower()}" in message.lower():
        return True
    
    # Respond to questions about Minecraft
    minecraft_keywords = [
        "craft", "recipe", "how do i", "how to make",
        "minecraft", "brewing", "enchant", "smelt",
        "pickaxe", "sword", "armor", "potion"
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in minecraft_keywords)


def clean_message(message: str) -> str:
    """Remove bot mentions and clean message"""
    # Remove @mentions
    cleaned = message.replace(f"@{BOT_NAME}", "").strip()
    cleaned = cleaned.replace(f"@{BOT_NAME.lower()}", "").strip()
    
    return cleaned


async def send_to_nextcloud(token: str, message: str):
    """Send message back to Nextcloud Talk"""
    url = f"{NEXTCLOUD_URL}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
    
    headers = {
        "OCS-APIRequest": "true",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NEXTCLOUD_TOKEN}"
    }
    
    data = {
        "message": message,
        "replyTo": 0
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 201:
            logger.info(f"✓ Message sent to conversation {token}")
        else:
            logger.error(f"Failed to send message: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error sending message to Nextcloud: {e}")


def format_answer_markdown(result: Dict) -> str:
    """Format RAG result as markdown for Nextcloud"""
    answer = result['answer']
    
    # Add sources if available
    if result.get('sources'):
        answer += "\n\n📚 **Sources:**"
        for source in result['sources'][:3]:
            answer += f"\n• [{source['title']}]({source['url']})"
    
    # Add cache indicator
    if result.get('cached'):
        answer += "\n\n*⚡ (from cache)*"
    
    return answer


@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """
    Handle incoming webhooks from Nextcloud Talk
    """
    logger.info("Webhook endpoint hit!")
    try:
        # Parse webhook data
        data = await request.json()
        logger.info(f"Received webhook: {data}")
        
        # Signature verification disabled for local Docker network deployment
        # In a local container-to-container setup, signature verification is not required
        # since the webhook endpoint is not exposed to external networks
        
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
        
        # Log query
        if cache:
            cache.log_query(query)
        
        # Check cache first
        cached_result = None
        if cache:
            cached_result = cache.get_cached_answer(query)
        
        if cached_result:
            logger.info("✓ Cache hit!")
            response_text = format_answer_markdown(cached_result)
            background_tasks.add_task(send_to_nextcloud, token, response_text)
            return {"status": "success", "cached": True}
        
        # Process with RAG pipeline
        logger.info("Querying RAG pipeline...")
        result = rag_pipeline.answer_question(query)
        
        # Cache the result
        if cache and result['answer']:
            cache.cache_answer(query, result['answer'], result.get('sources'))
        
        # Format and send response
        response_text = format_answer_markdown(result)
        background_tasks.add_task(send_to_nextcloud, token, response_text)
        
        return {"status": "success", "cached": False}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/test-query")
async def test_query(query: str):
    """Test endpoint for debugging (no Nextcloud required)"""
    logger.info(f"Test query: {query}")
    
    # Check cache
    cached_result = cache.get_cached_answer(query) if cache else None
    
    if cached_result:
        return {"result": cached_result, "source": "cache"}
    
    # Query RAG
    result = rag_pipeline.answer_question(query)
    
    return {"result": result, "source": "rag"}


@app.get("/stats")
async def get_stats():
    """Get bot statistics"""
    stats = {
        "cache_stats": cache.get_cache_stats() if cache else {},
        "popular_queries": cache.get_popular_queries(10) if cache else []
    }
    
    if vector_db:
        stats["vector_db_stats"] = vector_db.get_collection_stats()
    
    return stats


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
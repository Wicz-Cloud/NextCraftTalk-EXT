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
import asyncio
import json
import base64

from vector_db import MinecraftVectorDB
from rag_pipeline import MinecraftRAGPipeline

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
            ollama_url=OLLAMA_URL,
            model_name=MODEL_NAME
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
            "rag_pipeline": rag_pipeline is not None
        }
    }
    
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
    """Clean and prepare message for processing"""
    # Remove bot mentions
    message = message.replace(f"@{BOT_NAME}", "").strip()
    message = message.replace(f"@{BOT_NAME.lower()}", "").strip()
    
    # Remove common prefixes
    prefixes_to_remove = ["hey", "hi", "hello", "bot"]
    message_lower = message.lower()
    for prefix in prefixes_to_remove:
        if message_lower.startswith(prefix + " "):
            message = message[len(prefix)+1:].strip()
            break
    
    return message


def verify_signature(raw_body: bytes, signature_header: str, random_header: str) -> bool:
    """Verify Nextcloud Talk webhook signature
    
    Per Nextcloud Talk docs: Create HMAC with SHA256 over the RANDOM header 
    and the request body using the shared secret.
    """
    if not signature_header:
        logger.warning("No signature header provided - accepting for local development")
        return True  # Allow unsigned for local testing
    
    if not SHARED_SECRET:
        logger.warning("No SHARED_SECRET configured - accepting unsigned requests")
        return True
    
    try:
        # Nextcloud Talk signs: RANDOM_HEADER + REQUEST_BODY
        message_to_sign = random_header.encode('utf-8') + raw_body
        
        # Create HMAC-SHA256 signature
        expected_signature = hmac.new(
            SHARED_SECRET.encode('utf-8'),
            message_to_sign,
            hashlib.sha256
        ).hexdigest()
        
        provided_signature = signature_header.lower().strip()
        
        logger.info(f"DEBUG: Random header: {random_header}")
        logger.info(f"DEBUG: Expected signature: {expected_signature[:16]}...")
        logger.info(f"DEBUG: Received signature: {provided_signature[:16]}...")
        
        if hmac.compare_digest(provided_signature, expected_signature.lower()):
            logger.info("✓ Webhook signature verified")
            return True
        else:
            logger.warning(f"Invalid webhook signature")
            return False
        
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False


def send_thinking_message(token: str) -> Optional[int]:
    """Send thinking message and return its ID"""
    base_url = f"{NEXTCLOUD_URL}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
    
    headers = {
        "OCS-APIRequest": "true",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {NEXTCLOUD_TOKEN}"
    }
    
    data = {
        "message": "🤔 Thinking...",
        "replyTo": 0
    }
    
    try:
        response = requests.post(base_url, headers=headers, json=data, timeout=10)
        logger.info(f"Thinking message POST status: {response.status_code}, text: {response.text[:200]}")
        if response.status_code == 201:
            response_data = response.json()
            message_id = response_data.get("ocs", {}).get("data", {}).get("id")
            logger.info(f"✓ Thinking message sent, ID: {message_id}")
            return message_id
        else:
            logger.error(f"Failed to send thinking message: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error sending thinking message: {e}")
        return None

async def send_to_nextcloud_fallback(token: str, message: str):
    """Fallback: send new message if editing fails"""
    base_url = f"{NEXTCLOUD_URL}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
    
    headers = {
        "OCS-APIRequest": "true",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {NEXTCLOUD_TOKEN}"
    }
    
    data = {
        "message": message,
        "replyTo": 0
    }
    
    def _send():
        try:
            response = requests.post(base_url, headers=headers, json=data, timeout=10)
            if response.status_code == 201:
                logger.info(f"✓ Fallback message sent to conversation {token}")
                return True
            else:
                logger.error(f"Failed to send fallback message: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error sending fallback message: {e}")
            return False
    
    await asyncio.to_thread(_send)


async def process_and_respond(token: str, query: str, thinking_message_id: int):
    """Process the query and send response, then delete thinking message"""
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

async def edit_message(token: str, message_id: int, new_message: str) -> bool:
    """Edit a message in Nextcloud Talk"""
    base_url = f"{NEXTCLOUD_URL}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
    edit_url = f"{base_url}/{message_id}"
    
    headers = {
        "OCS-APIRequest": "true",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {NEXTCLOUD_TOKEN}"
    }
    
    data = {
        "message": new_message
    }
    
    try:
        response = requests.put(edit_url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            logger.info(f"✓ Message updated in conversation {token}")
            return True
        else:
            logger.error(f"Failed to edit message: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error editing message: {e}")
        return False

async def delete_message(token: str, message_id: int) -> bool:
    """Delete a message in Nextcloud Talk"""
    base_url = f"{NEXTCLOUD_URL}/ocs/v2.php/apps/spreed/api/v1/chat/{token}"
    delete_url = f"{base_url}/{message_id}"
    
    headers = {
        "OCS-APIRequest": "true",
        "Authorization": f"Bearer {NEXTCLOUD_TOKEN}"
    }
    
    def _delete():
        try:
            response = requests.delete(delete_url, headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info(f"✓ Message deleted in conversation {token}")
                return True
            else:
                logger.error(f"Failed to delete message: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error deleting message: {e}")
            return False
    
    return await asyncio.to_thread(_delete)


def format_answer_markdown(result: Dict) -> str:
    """Format RAG result as markdown for Nextcloud"""
    answer = result['answer']
    
    # Add sources if available
 #   if result.get('sources'):
 #       answer += "\n\n📚 **Sources:**"
 #       for source in result['sources'][:3]:
 #           answer += f"\n• [{source['title']}]({source['url']})"
    
    return answer


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
    uvicorn.run(app, host="0.0.0.0", port=8000)
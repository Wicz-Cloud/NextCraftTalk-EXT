# Nextcloud Configuration
NEXTCLOUD_URL=https://your-nextcloud.example.com
NEXTCLOUD_BOT_TOKEN=your-bot-token-here

# Bot Configuration
BOT_NAME=MinecraftBot
BOT_DISPLAY_NAME=Minecraft Helper

# LLM Configuration
OLLAMA_URL=http://ollama:11434
MODEL_NAME=phi3:mini

# Alternative model options:
# MODEL_NAME=gemma2:2b
# MODEL_NAME=mistral:7b-instruct
# MODEL_NAME=llama3:8b-instruct

# RAG Configuration
TOP_K_RESULTS=5
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Cache Configuration
ENABLE_CACHE=true
CACHE_DB_PATH=recipe_cache.db

# Performance Settings (for Raspberry Pi)
MAX_WORKERS=2
BATCH_SIZE=50
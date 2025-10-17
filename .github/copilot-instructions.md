# AI Coding Assistant Instructions for Minecraft Wiki RAG Chatbot

## Project Overview
This is a self-hosted Minecraft Wiki chatbot using Retrieval-Augmented Generation (RAG) with local LLMs. It integrates with Nextcloud Talk to answer Minecraft questions by retrieving relevant wiki content and generating responses via Ollama.

## Architecture
- **FastAPI Service** (`nextcloud_bot.py`): Webhook handler for Nextcloud Talk integration
- **RAG Pipeline** (`rag_pipeline.py`): Vector search + LLM generation using Ollama
- **Vector Database** (`vector_db.py`): ChromaDB with sentence-transformers embeddings
- **Data Pipeline** (`wiki_scraper.py`): Scrapes and chunks Minecraft Wiki content

## Key Workflows

### Initial Setup
```bash
# Unified setup and deployment script
chmod +x deploy-and-setup.sh
./deploy-and-setup.sh docker production
```
- Creates virtual environment, installs dependencies
- Scrapes Minecraft Wiki data (10-30 minutes)
- Builds ChromaDB vector database with embeddings

### Development Testing
```bash
# Test RAG pipeline directly
python rag_pipeline.py

# Test API endpoints
curl http://localhost:8000/health
curl -X POST "http://localhost:8000/test-query?query=How%20to%20craft%20diamond%20sword"
```

### Deployment
- **Docker (Recommended)**: `docker-compose up -d` runs Ollama + bot services
- **Local**: `python nextcloud_bot.py` (requires Ollama installed)
- **Health Check**: `curl http://localhost:8000/health`

## Code Patterns & Conventions

### Configuration
- Environment variables via `.env` file (copy from `.env.example`)
- Critical vars: `NEXTCLOUD_URL`, `NEXTCLOUD_BOT_TOKEN`, `MODEL_NAME`
- Models: `phi3:mini` (fast), `mistral:7b-instruct` (quality), `llama3:8b-instruct` (best)

### Response Formatting
- Use markdown with bullet points for recipes
- Format: `• 3 Diamonds\n• 2 Sticks`
- Include sources: `📚 Sources:\n• [Title](url)`

### Error Handling
- Health checks in FastAPI endpoints
- Graceful degradation when LLM unavailable
- Background tasks for async Nextcloud responses
- Structured logging to `logs/nextcloud_bot.log`

### Vector Search
- ChromaDB with sentence-transformers (`all-MiniLM-L6-v2`)
- Top-k retrieval (default 2-5 results)
- Similarity filtering (>0.1 threshold)
- Context limiting (2000 chars max) for LLM prompts

### LLM Integration
- Ollama API at `http://localhost:11434`
- Prompt engineering with context chunks
- Temperature 0.3 for consistent answers
- Response length limits (200 tokens)

## Integration Points

### Nextcloud Talk
- Webhook endpoint: `POST /webhook`
- ActivityPub format parsing
- Bot mention detection: `@MinecraftBot`
- Keyword triggers: "craft", "recipe", "how do i", "minecraft"

### External Dependencies
- **Ollama**: Local LLM server (runs in Docker)
- **ChromaDB**: Vector database (persistent storage)
- **Minecraft Wiki**: Data source via API scraping
- **Sentence Transformers**: Embedding model

## Development Guidelines

### Adding New Features
1. Test components individually first
2. Add health checks for new endpoints
3. Follow async patterns for external API calls

### Performance Considerations
- Limit context length in RAG prompts
- Use background tasks for slow operations
- Monitor with `/stats` endpoint

### Debugging
- Check logs: `tail -f logs/nextcloud_bot.log`
- Test endpoints: `curl http://localhost:8000/test-query`
- View stats: `curl http://localhost:8000/stats`
- Simulate webhooks with curl requests

## File Organization
- `wiki_data/`: Scraped and processed wiki content
- `chroma_db/`: Vector database storage
- `logs/`: Application logs
- `backups/`: Data backups
- `test_chroma_db/`: Test database instances</content>
<parameter name="filePath">/home/bill/mc_ai/.github/copilot-instructions.md

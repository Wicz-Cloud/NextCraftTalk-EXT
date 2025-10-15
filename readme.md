# 🎮 Minecraft Wiki RAG Chatbot for Nextcloud Talk

A self-hosted, open-source chatbot that answers Minecraft questions using RAG (Retrieval-Augmented Generation) with local LLMs. Optimized for kids with simple, fun responses. Fully integrated with Nextcloud Talk.

## 🌟 Features

- **Multi-Source Knowledge Base**: Scrapes Minecraft Wiki, official tips, crafting guides, and beginner tutorials
- **Fast Multi-threaded Processing**: Parallel scraping and vector embedding for quick setup
- **Kid-Friendly Responses**: Simple language, fun tone, clear steps suitable for 10-year-olds
- **Smart UX**: Shows "Thinking..." indicator while processing, then delivers clean answers
- **RAG Pipeline**: Retrieves relevant information and generates accurate answers
- **Local LLM**: Runs entirely on your hardware (no cloud APIs)
- **Nextcloud Talk Integration**: Responds naturally in chat conversations
- **Lightweight**: Runs on Raspberry Pi 5 with 8GB RAM
- **Modern Python**: Uses pyproject.toml, type hints, and comprehensive testing

## 🏗️ Architecture

```
User Query → Nextcloud Talk → Webhook → FastAPI Bot
                                           ↓
                                  Vector DB Search
                                           ↓
                                    Context Retrieval
                                           ↓
                                    LLM Generation
                                           ↓
                                    Response → Talk
```

## 📋 Requirements

### Hardware
- **Minimum**: 4GB RAM, 2 CPU cores, 20GB storage
- **Recommended**: 8GB RAM, 4 CPU cores, 50GB storage
- **Raspberry Pi**: Works on Pi 5 with 8GB RAM

### Software
- Python 3.11+ (3.13 recommended for latest packages)
- Docker & Docker Compose (optional but recommended)
- Ollama (for local LLM)
- Nextcloud instance with Talk app

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/webwicz/mc_ai.git
cd mc_ai

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 2. Development Setup

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
black .
ruff check .
mypy src/
```

### 3. Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up --build
```

### 4. Data Setup

```bash
# Scrape Minecraft wiki data
python -m src.data.scraper

# Setup vector database
python -m src.data.vector_db
```

## 📁 Project Structure

```
mc_ai/
├── src/                          # Source code
│   ├── __init__.py
│   ├── bot/                      # Bot components
│   │   ├── __init__.py
│   │   ├── __main__.py           # CLI entry point
│   │   ├── api.py                # FastAPI application
│   │   ├── message.py            # Message processing
│   │   ├── nextcloud_api.py      # Nextcloud Talk API client
│   │   └── security.py           # Webhook security
│   ├── core/                     # Core utilities
│   │   ├── __init__.py
│   │   └── config.py             # Configuration management
│   ├── data/                     # Data processing
│   │   ├── __init__.py
│   │   ├── scraper.py            # Wiki scraping
│   │   └── vector_db.py          # Vector database
│   └── rag/                      # RAG pipeline
│       ├── __init__.py
│       └── pipeline.py           # RAG implementation
├── tests/                        # Test suite
│   ├── __init__.py
│   └── test_*.py
├── docs/                         # Documentation
│   ├── deployment_guide.md
│   └── quick_reference.md
├── scripts/                      # Utility scripts
│   ├── deploy-and-setup.sh
│   └── maintenance.sh
├── docker/                       # Docker configuration
│   ├── Dockerfile
│   └── docker-compose.yml
├── .env.example                  # Environment template
├── pyproject.toml                # Modern Python packaging
├── .pre-commit-config.yaml       # Code quality hooks
└── README.md
```

# Run unified setup and deployment script
chmod +x deploy-and-setup.sh
./deploy-and-setup.sh docker production
```

The script will automatically:
- Detect if initial setup is needed
- Create virtual environment and install dependencies
- Scrape Minecraft knowledge base from multiple sources (Wiki, official tips, crafting guides)
- Build vector database with multi-threaded processing
- Deploy the bot

### 2. Configure Environment

Edit `.env` with your Nextcloud credentials (the script will create this file for you):

```env
NEXTCLOUD_URL=https://your-nextcloud.com
NEXTCLOUD_BOT_TOKEN=your-bot-token-here
SHARED_SECRET=your-shared-secret-here  # Required for webhook signature verification
BOT_NAME=MinecraftBot
MODEL_NAME=phi3:mini
```

### 3. Deploy

**Option A: Docker Compose (Recommended)**

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f minecraft_bot

# Check health
curl http://localhost:8000/health

# View logs
tail -f logs/nextcloud_bot.log
```

**Option B: Local Development**

```bash
# Activate virtual environment
source venv/bin/activate

# Start Ollama (in separate terminal)
ollama serve

# Pull model
ollama pull phi3:mini

# Run bot
python nextcloud_bot.py
```

## 🔒 Security

The bot implements HMAC-SHA256 signature verification for Nextcloud Talk webhooks to ensure request authenticity:

- **SHARED_SECRET**: Configure this environment variable with your Nextcloud Talk webhook secret
- **Signature Verification**: All webhook requests are verified using HMAC-SHA256
- **Fallback**: For local development, unsigned requests are accepted with warnings
- **Secure Headers**: Uses proper authorization headers for Nextcloud API calls

### 4. Configure Nextcloud Talk

1. Open Nextcloud Talk settings
2. Navigate to **Administration → Talk**
3. Go to **Bots** section
4. Add webhook:
   - **Webhook URL**: `http://your-server:8000/webhook`
   - **Bot Name**: `MinecraftBot`
   - **Description**: Minecraft Wiki Assistant
5. Save configuration

### 5. Test the Bot

In any Nextcloud Talk conversation:

```
@MinecraftBot How do I craft a diamond pickaxe?
```

Or just ask naturally:

```
What's the recipe for a brewing stand?
How do I enchant items?
```

## 📁 Project Structure

```
minecraft-wiki-bot/
├── wiki_scraper.py        # Scrapes Minecraft Wiki
├── vector_db.py           # ChromaDB vector database
├── rag_pipeline.py        # RAG retrieval & LLM
├── nextcloud_bot.py       # FastAPI webhook handler
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container image
├── docker-compose.yml    # Multi-service deployment
├── .env.example          # Configuration template
├── deploy-and-setup.sh   # Unified setup & deployment script
├── maintenance.sh        # Maintenance and monitoring tools
└── README.md             # This file
```

## 🔧 Configuration

### LLM Models

Choose a model based on your hardware:

| Model | RAM | Speed | Quality |
|-------|-----|-------|---------|
| `phi3:mini` | 4GB | Fast | Good |
| `gemma2:2b` | 4GB | Fast | Good |
| `mistral:7b-instruct` | 8GB | Medium | Better |
| `llama3:8b-instruct` | 8GB | Medium | Best |

Change model in `.env`:
```env
MODEL_NAME=phi3:mini
```

Pull new model:
```bash
ollama pull gemma2:2b
```

### RAG Parameters

Adjust in `.env`:

```env
TOP_K_RESULTS=5          # Number of context chunks
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## 🧪 Testing

### Test RAG Pipeline

```bash
# Test vector search and generation
python rag_pipeline.py
```

### Test API Endpoint

```bash
# Health check
curl http://localhost:8000/health

# Test query without Nextcloud
curl -X POST "http://localhost:8000/test-query?query=How%20to%20craft%20diamond%20sword"

# View statistics
curl http://localhost:8000/stats
```

### Test Nextcloud Integration

```bash
# Simulate webhook (replace TOKEN)
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I craft a golden apple?",
    "token": "conversation_token",
    "actor_id": "user123",
    "actor_displayname": "Test User"
  }'
```

## 📊 Monitoring

### View Logs

```bash
# Docker
docker-compose logs -f minecraft_bot

# Local
tail -f logs/bot.log
```

### Check Statistics

```bash
# Bot statistics
curl http://localhost:8000/stats
```

### Performance Metrics

Monitor resource usage:

```bash
# Docker
docker stats minecraft_bot

# System (Linux)
htop
```

## 🎯 Usage Examples

### Basic Crafting Questions

```
User: How do I craft a diamond pickaxe?
Bot: To craft a diamond pickaxe, you need:
• 3 Diamonds
• 2 Sticks

Place the 3 diamonds across the top row of the crafting grid, 
and place 2 sticks vertically down the middle column below them.

📚 Sources:
• [Diamond Pickaxe](https://minecraft.wiki/w/Diamond_Pickaxe)
```

### Brewing Questions

```
User: What's the recipe for a brewing stand?
Bot: To craft a brewing stand, you need:
• 1 Blaze Rod
• 3 Cobblestone

Place the blaze rod in the center slot and the 3 cobblestone 
across the bottom row of the crafting grid.

📚 Sources:
• [Brewing Stand](https://minecraft.wiki/w/Brewing_Stand)
```

### Complex Questions

```
User: How do I enchant a sword with sharpness?
Bot: To enchant a sword with Sharpness:

1. Build an Enchanting Table (requires 4 obsidian, 2 diamonds, 1 book)
2. Place bookshelves around it (up to 15 for max level enchants)
3. Place your sword in the enchanting table
4. Select an enchantment option that shows Sharpness
5. Spend the required XP levels

Alternatively, you can combine enchanted books with Sharpness 
using an anvil.

📚 Sources:
• [Enchanting](https://minecraft.wiki/w/Enchanting)
• [Sharpness](https://minecraft.wiki/w/Sharpness)
```

## 🔒 Security

### API Token Security

1. **Never commit** `.env` to version control
2. Use strong, random tokens for `NEXTCLOUD_BOT_TOKEN`
3. Restrict webhook access with firewall rules

### Network Security

Use reverse proxy (Nginx) with HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name bot.yourdomain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    location / {
        proxy_pass http://minecraft_bot:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Nextcloud Restrictions

Configure Talk to only accept webhooks from authenticated sources:

1. Enable "Require authentication" in Talk settings
2. Use IP whitelisting if possible
3. Monitor webhook activity in logs

## 🐛 Troubleshooting

### Bot Not Responding

**Check health endpoint:**
```bash
curl http://localhost:8000/health
```

**Verify Ollama is running:**
```bash
curl http://localhost:11434/api/tags
```

**Check logs:**
```bash
docker-compose logs minecraft_bot
```

### Vector DB Issues

**Rebuild database:**
```bash
python vector_db.py
# When prompted, type 'yes' to reset
```

**Check collection:**
```python
from vector_db import MinecraftVectorDB
db = MinecraftVectorDB()
print(db.get_collection_stats())
```

### Model Loading Errors

**Pull model manually:**
```bash
ollama pull phi3:mini
```

**List available models:**
```bash
ollama list
```

**Try smaller model:**
```env
MODEL_NAME=gemma2:2b
```

### Nextcloud Webhook Issues

**Test webhook manually:**
```bash
curl -X POST http://your-bot:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": "test",
    "token": "test_token",
    "actor_id": "test_user"
  }'
```

**Check Nextcloud logs:**
```bash
docker exec -it nextcloud tail -f /var/www/html/data/nextcloud.log
```

### Memory Issues (Raspberry Pi)

**Use smaller model:**
```env
MODEL_NAME=phi3:mini
```

**Reduce batch size:**
```env
BATCH_SIZE=25
TOP_K_RESULTS=3
```

**Enable swap:**
```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=4096
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## 🔄 Updating

### Update Wiki Data

Re-scrape the wiki periodically:

```bash
# Backup existing data
cp -r wiki_data wiki_data.backup
cp -r chroma_db chroma_db.backup

# Re-scrape
python wiki_scraper.py

# Rebuild vector DB
python vector_db.py  # Select 'yes' to reset
```

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Update Docker Images

```bash
docker-compose pull
docker-compose up -d
```

## 🎨 Customization

### Modify Response Format

Edit `rag_pipeline.py` to change prompt template:

```python
def build_prompt(self, query: str, context_docs: List[Dict]) -> str:
    # Customize this method to change response style
    prompt = f"""Your custom instructions here...
    
    CONTEXT: {context}
    QUESTION: {query}
    ANSWER:"""
    return prompt
```

### Add New Commands

Extend `nextcloud_bot.py`:

```python
@app.post("/custom-command")
async def custom_handler(request: Request):
    # Your custom logic
    pass
```

## 📈 Performance Optimization

### For Raspberry Pi

1. **Use lightweight model**: `phi3:mini` or `gemma2:2b`
2. **Enable caching**: Set `ENABLE_CACHE=true`
3. **Reduce context**: Set `TOP_K_RESULTS=3`
4. **Pre-generate embeddings**: Run scraper offline
5. **Use SSD storage**: For faster vector search

### For Production Server

1. **Use powerful model**: `llama3:8b-instruct`
2. **Increase context**: Set `TOP_K_RESULTS=7`
3. **Add GPU support**: Uncomment GPU section in `docker-compose.yml`
4. **Scale with replicas**: Use multiple bot instances behind load balancer

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Add support for more wiki sources
- [ ] Implement conversation history
- [ ] Add image recognition for recipe screenshots
- [ ] Create web UI for administration
- [ ] Add multilingual support
- [ ] Optimize for edge devices

## 📜 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- [Minecraft Wiki](https://minecraft.wiki) - Knowledge source
- [Ollama](https://ollama.ai) - Local LLM serving
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [Sentence Transformers](https://www.sbert.net/) - Embeddings
- [Nextcloud](https://nextcloud.com) - Self-hosted collaboration

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/minecraft-wiki-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/minecraft-wiki-bot/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/minecraft-wiki-bot/wiki)

---

## 📝 Changelog

### Latest Updates (October 2025)
- ✅ **Removed cache functionality** - Simplified architecture, removed cache-related code
- ✅ **Expanded knowledge sources** - Added official Minecraft tips, crafting.net, Instructables, Minecraft Beginners Guide
- ✅ **Multi-threaded performance** - Parallel scraping (5 wiki threads, 3 URL threads) and vector DB processing (4 worker threads)
- ✅ **Kid-friendly optimization** - Responses use simple language, fun tone, clear steps for 10-year-olds
- ✅ **Enhanced UX** - "Thinking..." indicator appears immediately, disappears after response
- ✅ **Increased response limits** - LLM token limit raised to 1000 for complete answers
- ✅ **Improved context filtering** - Stricter prompts to ignore non-Minecraft content

---

## 🗺️ Roadmap

### Version 1.1
- [ ] Conversation context/memory
- [ ] Multi-language support
- [ ] Image-based recipe queries
- [ ] Voice command support

### Version 2.0
- [ ] Integration with Minecraft servers (RCON)
- [ ] In-game bot via Mineflayer
- [ ] Recipe recommendations
- [ ] Achievement tracking

---

**Made with ❤️ for the Minecraft community**
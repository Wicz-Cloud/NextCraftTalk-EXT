# 🎮 Minecraft Wiki RAG Chatbot

A self-hosted chatbot that answers Minecraft questions using RAG (Retrieval-Augmented Generation) with local LLMs. Optimized for kids with simple, fun responses. Fully integrated with Nextcloud Talk.

## ✨ Features

- **Smart Minecraft Knowledge**: Answers crafting recipes, gameplay questions, and Minecraft mechanics
- **Kid-Friendly**: Simple language and clear steps suitable for children
- **Local AI**: Runs entirely on your hardware using Ollama
- **Nextcloud Talk Integration**: Responds naturally in chat conversations
- **Fast Setup**: One-command deployment with Docker
- **Lightweight**: Runs on Raspberry Pi 5 with 8GB RAM
- **Dynamic Prompts**: Edit bot personality without container restarts
- **Auto-Reload**: Prompt changes detected automatically via file watching

## 🚀 Quick Start

### 1. Deploy Everything

```bash
# Clone and deploy in one command
git clone <your-repo> && cd mc_ai
chmod +x scripts/deployment.sh
./scripts/deployment.sh docker production
```

The deployment script automatically:
- Sets up Docker containers (bot + Ollama)
- **Configures networks** based on your `NETWORK_NAME` setting
- Scrapes Minecraft wiki data
- Builds knowledge base
- Configures the bot

### 2. Configure Nextcloud

1. Go to **Settings → Administration → Talk → Bots**
2. Add webhook: `http://your-server:8000/webhook`
3. Set bot name: `MinecraftBot`

### 3. Test the Bot

In any Nextcloud Talk conversation:

```
@MinecraftBot How do I craft a diamond pickaxe?
```

## 🎯 Usage Examples

### Basic Crafting
```
User: How do I craft a diamond pickaxe?
Bot: To craft a diamond pickaxe, you need:
• 3 Diamonds
• 2 Sticks

Place the 3 diamonds across the top row of the crafting grid,
and place 2 sticks vertically down the middle column below them.

📚 Sources: Minecraft Wiki
```

### Brewing & Potions
```
User: What's the recipe for a brewing stand?
Bot: To craft a brewing stand, you need:
• 1 Blaze Rod
• 3 Cobblestone

Place the blaze rod in the center slot and the 3 cobblestone
across the bottom row of the crafting grid.

📚 Sources: Minecraft Wiki
```

### Enchanting
```
User: How do I enchant a sword with sharpness?
Bot: To enchant a sword with Sharpness:

1. Build an Enchanting Table (obsidian + diamonds + book)
2. Place bookshelves around it (15 max for best enchants)
3. Place your sword in the enchanting table
4. Select Sharpness enchantment option

📚 Sources: Minecraft Wiki
```

### Natural Conversation
The bot responds to natural language:

```
What's the best way to find diamonds?
How do I make a beacon?
Tell me about golden apples
What's the recipe for an anvil?
```

## 📋 Requirements

- **Hardware**: 4GB RAM minimum, 8GB recommended
- **Software**: Docker, Python 3.11+, Linux/macOS
- **Network**: Internet for initial setup, Nextcloud instance

## 🛠️ Configuration

Edit `.env` file:

```env
# Nextcloud Settings
NEXTCLOUD_URL=https://your-nextcloud.com
NEXTCLOUD_BOT_TOKEN=your-bot-token-here

# Docker Network (choose based on your Nextcloud setup)
NETWORK_NAME=nextcloud-aio  # For Nextcloud AIO
# NETWORK_NAME=bridge       # For standalone Nextcloud + nginx

# Bot Settings
BOT_NAME=MinecraftBot
MODEL_NAME=gemma2:2b       # Current model (phi3:mini, gemma2:2b, mistral:7b-instruct)
OLLAMA_PORT=11434          # Ollama API port
BOT_PORT=8111              # Bot API port

# Prompt Template (external file for easy editing)
PROMPT_TEMPLATE_PATH=prompt_template.txt

# Performance (adjust for your hardware)
TOP_K_RESULTS=5
BATCH_SIZE=50
```

### 🎭 Customizing Bot Personality

The bot's personality and response style can be customized by editing `prompt_template.txt`:

```bash
# Edit the prompt template
nano prompt_template.txt

# Changes are automatically detected - no restart needed!
# Or manually reload via API: curl -X POST http://localhost:8111/reload-prompt
```

**Template Format:**
- `{context}` - Inserted with relevant Minecraft knowledge
- `{query}` - The user's question
- Everything else is your custom prompt instructions

**Example:**
```txt
You are a fun Minecraft buddy for kids!

MINECRAFT INFO:
{context}

QUESTION:
{query}

HELPFUL RESPONSE:
- Talk like a cool friend, not a robot.
- Keep it simple and exciting!
- Focus on Minecraft only.
- Show crafting recipes in grids.
- Make it easy to follow.
```

## 🔧 Management

### Docker Commands
```bash
# View logs
docker-compose logs -f minecraft_bot

# Restart bot
docker-compose restart minecraft_bot

# Update
docker-compose pull && docker-compose up -d

# Rebuild after code changes
docker-compose build minecraft_bot && docker-compose up -d minecraft_bot
```

### API Endpoints
```bash
# Health check
curl http://localhost:8111/health

# Get statistics
curl http://localhost:8111/stats

# Manual prompt reload (if file watching fails)
curl -X POST http://localhost:8111/reload-prompt

# Test query (development)
curl -X POST http://localhost:8111/test-query -H "Content-Type: application/json" -d '{"query": "How to craft a sword?"}'
```

### Prompt Management
```bash
# Edit prompt template (changes auto-detected)
nano prompt_template.txt

# View current prompt
cat prompt_template.txt

# Backup current prompt
cp prompt_template.txt prompt_template.txt.backup
```

## 🏗️ Architecture

### Components
- **FastAPI Bot**: Handles Nextcloud webhooks and API requests
- **RAG Pipeline**: Combines vector search with LLM generation
- **Vector Database**: ChromaDB stores Minecraft knowledge embeddings
- **Ollama**: Local LLM server for text generation
- **File Watcher**: Automatically detects prompt template changes

### Data Flow
1. User asks question in Nextcloud Talk
2. Webhook triggers bot API
3. Query embedded and searched in vector DB
4. Relevant Minecraft knowledge retrieved
5. Prompt template loaded (with auto-reload capability)
6. LLM generates kid-friendly response
7. Response sent back to Nextcloud

### File Watching
The bot uses `watchdog` library to monitor `prompt_template.txt` for changes:
- **Automatic**: Changes detected immediately, no restart needed
- **Manual**: API endpoint available for forced reload
- **Fallback**: Default prompt used if file loading fails

## 🐛 Troubleshooting

**Bot not responding?**
```bash
# Check health
curl http://localhost:8111/health

# Check logs
docker-compose logs -f minecraft_bot

# Test Ollama connection
curl http://localhost:11434/api/tags
```

**Prompt changes not taking effect?**
```bash
# Check if file watcher is running (look for "👀 Started watching" in logs)
docker-compose logs minecraft_bot | grep "watching"

# Manual reload
curl -X POST http://localhost:8111/reload-prompt

# Verify prompt file exists and is mounted
docker-compose exec minecraft_bot ls -la /app/prompt_template.txt
```

**Model not working?**
```bash
# Check available models
curl http://localhost:11434/api/tags

# Pull a model
docker-compose exec ollama ollama pull gemma2:2b

# Change model in .env and restart
echo "MODEL_NAME=gemma2:2b" >> .env
docker-compose restart minecraft_bot
```

**Permission issues?**
```bash
# Fix file permissions
sudo chown -R $USER:$USER /home/bill/mc_ai
chmod 644 prompt_template.txt
```

**Container won't start?**
```bash
# Clean rebuild
docker-compose down
docker system prune -f
docker-compose up -d --build
```

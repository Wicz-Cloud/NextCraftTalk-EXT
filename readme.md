# 🎮 Minecraft Wiki RAG Chatbot

A self-hosted chatbot that answers Minecraft questions using RAG (Retrieval-Augmented Generation) with local LLMs. Optimized for kids with simple, fun responses. Fully integrated with Nextcloud Talk.

## ✨ Features

- **Smart Minecraft Knowledge**: Answers crafting recipes, gameplay questions, and Minecraft mechanics
- **Kid-Friendly**: Simple language and clear steps suitable for children
- **Local AI**: Runs entirely on your hardware using Ollama
- **Nextcloud Talk Integration**: Responds naturally in chat conversations
- **Fast Setup**: One-command deployment with Docker
- **Lightweight**: Runs on Raspberry Pi 5 with 8GB RAM

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
MODEL_NAME=phi3:mini  # or gemma2:2b, mistral:7b-instruct

# Performance (adjust for your hardware)
TOP_K_RESULTS=5
BATCH_SIZE=50
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
```

### Maintenance
```bash
# Interactive maintenance menu
./scripts/maintenance.sh

# Update wiki data
python -m src.data.scraper

# Rebuild knowledge base
python -m src.data.vector_db
```

## 🐛 Troubleshooting

**Bot not responding?**
```bash
# Check health

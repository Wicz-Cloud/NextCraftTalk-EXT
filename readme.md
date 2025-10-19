# 🎮 NextCraftTalk-EXT

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=flat&logo=docker&logoColor=white)](https://docker.com/)

A self-hosted Minecraft knowledge chatbot that answers questions using x.ai's Grok model directly. No local knowledge base required - leverages x.ai's comprehensive understanding of Minecraft for kid-friendly responses. Fully integrated with Nextcloud Talk for natural chat conversations.

## 📋 Table of Contents

- [🎮 Minecraft AI Chatbot](#-minecraft-ai-chatbot)
  - [📋 Table of Contents](#-table-of-contents)
  - [✨ Features](#-features)
  - [🚀 Quick Start](#-quick-start)
  - [📦 Installation](#-installation)
  - [⚙️ Configuration](#️-configuration)
  - [🎯 Usage](#-usage)
  - [🔧 API Reference](#-api-reference)
  - [🐛 Troubleshooting](#-troubleshooting)
  - [🤝 Contributing](#-contributing)
  - [📜 Code of Conduct](#-code-of-conduct)
  - [� Security](#-security)
  - [�📄 License](#-license)
  - [🙏 Acknowledgments](#-acknowledgments)

## ✨ Features

- **🤖 Direct x.ai Integration** - Uses x.ai's Grok model directly for all responses
- **🚫 No Local Storage** - No vector database or scraped data required
- **👶 Kid-Friendly** - Simple language and clear steps suitable for children
- **☁️ Cloud AI** - Leverages x.ai's powerful language model
- **💬 Nextcloud Talk Integration** - Responds naturally in chat conversations
- **⚡ Fast Setup** - One-command deployment with Docker
- **🎭 Dynamic Prompts** - Edit bot personality without container restarts
- **👀 Auto-Reload** - Prompt changes detected automatically via file watching
- **🔊 Configurable Logging** - Control verbosity levels for monitoring

## 🚀 Quick Start

Get the Minecraft AI Chatbot running in under 5 minutes!

### Prerequisites

- Docker and Docker Compose
- Nextcloud instance with Talk enabled
- x.ai API key ([get one here](https://x.ai))

### Deploy

```bash
# Clone the repository
git clone https://github.com/Wicz-Cloud/NextCraftTalk-EXT.git && cd NextCraftTalk-EXT

# Start the bot
docker-compose up -d

# Check it's running
docker-compose logs -f minecraft_bot
```

### Configure

1. **Get x.ai API Key**: Visit [x.ai](https://x.ai) and obtain your API key
2. **Configure Environment**: Edit `.env` file with your settings
3. **Test the Bot**: Mention `@MinecraftBot` in any Nextcloud Talk conversation

```bash
@MinecraftBot How do I craft a diamond pickaxe?
```

## 📦 Installation

### Option 1: Docker Compose (Recommended)

```bash
# Clone repository
git clone https://github.com/Wicz-Cloud/NextCraftTalk-EXT.git
cd NextCraftTalk-EXT

# Start services
docker-compose up -d

# View logs
docker-compose logs -f minecraft_bot
```

### Option 2: Manual Installation

```bash
# Clone repository
git clone https://github.com/Wicz-Cloud/NextCraftTalk-EXT.git
cd NextCraftTalk-EXT

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run the bot
python -m src.bot
```

### System Requirements

- **OS**: Linux, macOS, or Windows with WSL2
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Internet connection for x.ai API

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Nextcloud Configuration
NEXTCLOUD_URL=https://your-nextcloud.com
NEXTCLOUD_BOT_TOKEN=your-bot-token-here

# x.ai Configuration
XAI_API_KEY=your-xai-api-key-here
MODEL_NAME=grok-4-fast-non-reasoning

# Bot Configuration
BOT_NAME=MinecraftBot
BOT_PORT=8111

# Optional: Network Configuration
NETWORK_NAME=nextcloud-aio

# Optional: Logging
LOG_LEVEL=INFO
```

### Nextcloud Setup

1. **Install Nextcloud Talk**: Ensure Talk app is installed and enabled
2. **Create Bot User**: Create a dedicated user account for the bot
3. **Generate Token**: Use Nextcloud's app password feature for secure access
4. **Configure Webhooks**: The bot automatically registers for Talk webhooks

### x.ai Setup

1. **Visit x.ai**: Go to [x.ai](https://x.ai) and create an account
2. **Get API Key**: Navigate to API settings and generate a new key
3. **Test Connection**: The bot will validate the key on startup

## 🎯 Usage

### Basic Commands

The bot responds to natural language questions in Nextcloud Talk:

```
@MinecraftBot How do I craft a diamond pickaxe?
@MinecraftBot What's the best way to find diamonds?
@MinecraftBot How do I make a beacon?
@MinecraftBot Tell me about golden apples
```

### Response Examples

**Crafting Recipe:**
```
User: How do I craft a diamond pickaxe?
Bot: To craft a diamond pickaxe, you need:
• 3 Diamonds
• 2 Sticks

Place the 3 diamonds across the top row of the crafting grid,
and place 2 sticks vertically down the middle column below them.

📚 Sources: Minecraft Wiki
```

**Enchanting Guide:**
```
User: How do I enchant a sword with sharpness?
Bot: To enchant a sword with Sharpness:

1. Build an Enchanting Table (obsidian + diamonds + book)
2. Place bookshelves around it (15 max for best enchants)
3. Place your sword in the enchanting table
4. Select Sharpness enchantment option

📚 Sources: Minecraft Wiki
```

### Advanced Features

#### Custom Bot Personality

Edit `prompt_template.txt` to customize the bot's personality:

```txt
You are a fun Minecraft buddy for kids!

QUESTION:
{query}

HELPFUL RESPONSE:
- Talk like a cool friend, not a robot.
- Keep it simple and exciting!
- Focus on Minecraft only.
- Show crafting recipes in grids.
- Make it easy to follow.
```

#### Logging Control

```bash
# Default logging (essential info only)
docker-compose up -d

# Verbose logging (detailed operations)
docker-compose exec minecraft_bot python -m src.bot --verbose

# Debug logging (everything)
docker-compose exec minecraft_bot python -m src.bot --verbose --debug
```

## 🔧 API Reference

### Health Check

```bash
GET /health
```

Returns bot status and configuration info.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "xai_connected": true,
  "nextcloud_connected": true
}
```

### Test Query

```bash
POST /test-query
Content-Type: application/json

{
  "query": "How to craft a sword?"
}
```

Test the bot without Nextcloud integration.

### Reload Prompt

```bash
POST /reload-prompt
```

Force reload of the prompt template file.

## 🐛 Troubleshooting

### Bot Not Responding

**Check Health:**
```bash
curl http://localhost:8111/health
```

**View Logs:**
```bash
docker-compose logs -f minecraft_bot
```

**Common Issues:**
- Verify x.ai API key is correct
- Check Nextcloud URL and token
- Ensure Docker network connectivity

### Connection Issues

**x.ai API Problems:**
```bash
# Test API key
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.x.ai/v1/models
```

**Nextcloud Issues:**
```bash
# Check Nextcloud Talk API
curl -H "Authorization: Bearer YOUR_TOKEN" https://your-nextcloud.com/ocs/v2.php/apps/spreed/api/v1/room
```

### Performance Issues

**High Memory Usage:**
- Reduce `TOP_K_RESULTS` in config
- Restart container

**Slow Responses:**
- Check internet connection
- Verify x.ai service status
- Consider upgrading to faster model

### File Permission Issues

```bash
# Fix permissions
sudo chown -R $USER:$USER /path/to/mc_ai
chmod 644 prompt_template.txt
chmod 755 docker/
```

### Container Won't Start

```bash
# Clean rebuild
docker-compose down
docker system prune -f
docker-compose up -d --build
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

### Development Setup

```bash
# Fork and clone
git clone https://github.com/Wicz-Cloud/NextCraftTalk-EXT.git
cd NextCraftTalk-EXT

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest

# Start development server
python -m src.bot --verbose --debug
```

### Pull Request Process

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Code Standards

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation
- Ensure all tests pass

## 📜 Code of Conduct

This project is governed by a [Code of Conduct](CODE_OF_CONDUCT.md) to ensure a welcoming environment for all contributors and users. By participating, you agree to uphold this code.

## � Security

For information about reporting security vulnerabilities, please see our [Security Policy](SECURITY.md).

## �📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Web Wizard

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- **x.ai** for providing the Grok language model
- **Nextcloud** for the Talk integration platform
- **Docker** for containerization technology
- **FastAPI** for the web framework
- **Minecraft Wiki** community for comprehensive documentation

---

<div align="center">

**Made with ❤️ for the NextCloud & Minecraft community**

[⭐ Star us on GitHub](https://github.com/Wicz-Cloud/NextCraftTalk-EXT) • [🐛 Report Issues](https://github.com/Wicz-Cloud/NextCraftTalk-EXT/issues) • [💬 Join Discussions](https://github.com/Wicz-Cloud/NextCraftTalk-EXT/discussions)

</div>

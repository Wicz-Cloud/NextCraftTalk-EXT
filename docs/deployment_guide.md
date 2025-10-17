# 📦 Minecraft Wiki Bot - Complete Deployment Guide

This guide walks you through deploying the Minecraft Wiki Bot from scratch to production.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Deployment Options](#deployment-options)
4. [Nextcloud Configuration](#nextcloud-configuration)
5. [Testing & Verification](#testing--verification)
6. [Production Checklist](#production-checklist)
7. [Troubleshooting](#troubleshooting)

---

## 1. Prerequisites

### Required

- **Server/Hardware**:
  - Minimum: 4GB RAM, 2 CPU cores, 20GB storage
  - Recommended: 8GB RAM, 4 CPU cores, 50GB storage
  - Raspberry Pi 5 with 8GB RAM (supported)

- **Software**:
  - Ubuntu 22.04+ / Debian 11+ / Raspberry Pi OS
  - Python 3.12 or higher (3.13 recommended)
  - Docker 24+ and Docker Compose (for Docker deployment)
  - Git

- **Network**:
  - Internet connection for downloading models and wiki data
  - Open port 8000 (or configure reverse proxy)
  - Access to your Nextcloud instance

### Optional but Recommended

- HTTPS/SSL certificate (Let's Encrypt)
- Domain name
- Nginx or Apache for reverse proxy

---

## 2. Initial Setup

### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip \
  git curl wget build-essential sqlite3

# Install Docker (if using Docker deployment)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin
```

**Raspberry Pi:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv git curl sqlite3

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Reboot to apply docker group
sudo reboot
```

### Step 2: Install Ollama

**Linux/Mac:**
```bash
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve &

# Pull recommended model
ollama pull phi3:mini
```

**Alternative Models:**
```bash
# Smaller model (2GB RAM)
ollama pull gemma2:2b

# Better quality (8GB RAM)
ollama pull llama3:8b-instruct
```

### Step 3: Clone Repository

```bash
# Create project directory
mkdir -p ~/minecraft-bot
cd ~/minecraft-bot

# Clone (or download) the project files
# Assuming files are in current directory
# Create necessary directories
mkdir -p wiki_data chroma_db backups logs
```

### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Minimum Required Configuration:**
```env
NEXTCLOUD_URL=https://your-nextcloud.example.com
NEXTCLOUD_BOT_TOKEN=your-generated-token-here
BOT_NAME=MinecraftBot
MODEL_NAME=phi3:mini
```

**Get Nextcloud Bot Token:**
Step 1: Create a Bot User Account

Go to User Management

Settings → Users (you need admin access)
Click "New user"
Create account:



     Username: minecraft-bot
     Display name: Minecraft Helper
     Email: (optional)

Log in as the bot user and generate an app password:

Go to Settings → Security → Devices & sessions
Create new app password named "Talk Bot"
Copy this password - this is your bot token!

---

## 3. Deployment Options

Choose the deployment method that best fits your environment.

### Unified Setup and Deployment (Recommended)

The enhanced deployment script combines setup and deployment into a single seamless workflow with safety checks:

```bash
# Make script executable
chmod +x scripts/deploy-enhanced.sh

# Run enhanced setup and deployment
./scripts/deploy-enhanced.sh docker production

# This will automatically:
# - Check for port/container/network conflicts
# - Detect if initial setup is needed
# - Create virtual environment and install dependencies
# - Scrape Minecraft knowledge base from multiple sources
# - Build vector database with multi-threaded processing
# - Pull required Ollama model
# - Deploy based on chosen method with health checks
```

**Available deployment types:**
- `docker` - Docker Compose deployment (default, recommended)
- `local` - Local deployment with Python virtual environment
- `pi` or `raspberry-pi` - Raspberry Pi optimized deployment

**Available environments:**
- `production` - Production mode with backups and tests (default)
- `development` - Development mode (skips backups and tests)

**Examples:**
```bash
# Docker deployment (production)
./scripts/deploy-enhanced.sh docker production

# Local deployment (development)
./scripts/deploy-enhanced.sh local development

# Raspberry Pi deployment
./scripts/deploy-enhanced.sh pi production
```

**Safety Features:**
- Port conflict detection (checks ports 8000, 11434)
- Container name conflict checking
- Network conflict prevention
- Automatic backup creation
- Health checks after deployment
- Rollback capability on failures

### Option A: Docker Deployment Details

```bash
# Build and start services
./deploy-and-setup.sh docker production

# Or manually:
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f minecraft_bot
```

**Docker Compose includes:**
- Ollama server (LLM)
- Minecraft Bot API
- Automatic restarts
- Health checks

### Option B: Local Development

```bash
# Use unified script
./deploy-and-setup.sh local development

# Or manually:
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Scrape wiki data
python -m src.data.scraper

# Build vector database
python -m src.data.vector_db

# Start bot
python -m src.bot.api
```

### Option C: Raspberry Pi Specific

```bash
# Use optimized deployment
./deploy-and-setup.sh pi production

# This configures:
# - Lightweight model (phi3:mini)
# - Reduced batch sizes
# - Lower resource limits
# - Temperature monitoring
```

---

## 4. Nextcloud Configuration

### Step 1: Access Nextcloud Admin Settings

1. Log in as administrator
2. Navigate to **Settings** → **Administration** → **Talk**

### Step 2: Configure Bot

1. Scroll to **"Bots"** section
2. Click **"Add Bot"**
3. Fill in details:
   - **Name**: `MinecraftBot`
   - **Display Name**: `Minecraft Helper`
   - **Description**: `Answers Minecraft crafting and gameplay questions`
   - **Webhook URL**: `http://your-server:8000/webhook`
     - Use HTTPS in production: `https://bot.yourdomain.com/webhook`
   - **Secret**: Leave empty (or set if you want extra auth)

### Step 3: Bot Configuration

**Webhook URL Format:**
- Local testing: `http://localhost:8000/webhook`
- Server: `http://your-server-ip:8000/webhook`
- Production: `https://bot.yourdomain.com/webhook`

**Important Notes:**
- Nextcloud must be able to reach the webhook URL
- If using Docker, ensure ports are exposed
- For remote servers, configure firewall to allow port 8000
- Use reverse proxy with HTTPS for production

### Step 4: Test Bot Access

```bash
# From Nextcloud server, test webhook
curl http://your-bot-server:8000/health

# Should return:
# {"status":"healthy","components":{"vector_db":true,"rag_pipeline":true}}
```

### Step 5: Add Bot to Conversation

1. Create or open a Talk conversation
2. Click "Add participants"
3. Search for `MinecraftBot`
4. Add the bot
5. Test with: `@MinecraftBot hello`

---

## 5. Testing & Verification

### Automated Tests

```bash
# Run comprehensive test suite
python test_bot.py

# Or use maintenance script
./scripts/maintenance.sh
# Select option 11 (Test Bot)
```

### Manual Testing

**Test API Endpoints:**
```bash
# Health check
curl http://localhost:8000/health

# Test query
curl -X POST "http://localhost:8000/test-query?query=How%20to%20craft%20diamond%20pickaxe"

# View statistics
curl http://localhost:8000/stats | python3 -m json.tool
```

**Test in Nextcloud Talk:**

1. **Mention Bot:**
   ```
   @MinecraftBot How do I craft a diamond pickaxe?
   ```

2. **Natural Questions:**
   ```
   What's the recipe for a brewing stand?
   How do I enchant items?
   Tell me about golden apples
   ```

3. **Expected Response:**
   - Bot should respond within 3-10 seconds
   - Answer should include recipe details
   - Sources should be linked
   - Markdown formatting should work

### Verification Checklist

- [ ] Bot appears in Talk conversations
- [ ] Bot responds to mentions (@MinecraftBot)
- [ ] Bot responds to Minecraft keywords
- [ ] Responses are accurate and well-formatted
- [ ] Sources are included and linked
- [ ] Health endpoint returns "healthy"
- [ ] Logs show no errors

---

## 6. Production Checklist

### Security

- [ ] Use HTTPS/SSL for webhook endpoint
- [ ] Secure NEXTCLOUD_BOT_TOKEN in .env
- [ ] Never commit .env to version control
- [ ] Configure firewall rules
- [ ] Use reverse proxy (Nginx/Apache)
- [ ] Enable fail2ban or similar
- [ ] Regular security updates

### Performance

- [ ] Appropriate model for hardware (see table below)
- [ ] Vector database is optimized
- [ ] Adequate disk space (monitor logs)
- [ ] Memory usage is stable
- [ ] Response times < 10 seconds

**Model Selection Guide:**

| Hardware | Recommended Model | RAM Usage | Response Time |
|----------|------------------|-----------|---------------|
| Pi 4 4GB | gemma2:2b | 2-3GB | 10-20s |
| Pi 5 8GB | phi3:mini | 3-4GB | 5-10s |
| Server 8GB | mistral:7b-instruct | 6-7GB | 3-8s |
| Server 16GB+ | llama3:8b-instruct | 8-10GB | 2-5s |

### Monitoring

- [ ] Set up log rotation
- [ ] Monitor disk usage
- [ ] Track response times
- [ ] Set up alerts for failures
- [ ] Regular backup schedule

```bash
# Enable systemd service
sudo systemctl enable minecraft-bot

# Set up log rotation
sudo nano /etc/logrotate.d/minecraft-bot
```

Add:
```
/home/user/minecraft-bot/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 user user
}
```

### Backup Strategy

```bash
# Automated daily backup (add to crontab)
crontab -e

# Add:
0 2 * * * cd /home/user/minecraft-bot && ./scripts/maintenance.sh backup
```

Or use maintenance script:
```bash
./scripts/maintenance.sh
# Select option 3 (Backup Data)
```

### Update Schedule

- **Weekly**: Check logs and stats
- **Monthly**: Update wiki data
- **Quarterly**: Update bot code and dependencies
- **As needed**: Rebuild vector database

---

## 7. Troubleshooting

### Bot Not Responding in Talk

**Check webhook configuration:**
```bash
# Test from Nextcloud server
curl -X POST http://bot-server:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": "@MinecraftBot test",
    "token": "test_token",
    "actor_id": "test_user",
    "actor_displayname": "Test"
  }'
```

**Check Nextcloud logs:**
```bash
# On Nextcloud server
tail -f /var/www/html/data/nextcloud.log | grep -i webhook
```

**Verify bot is in conversation:**
- Check Talk conversation participants
- Bot should be listed as participant
- Try removing and re-adding bot

### Slow Responses

**Check system resources:**
```bash
# Docker
docker stats minecraft_bot

# Local
htop
```

**Optimize for speed:**
1. Use smaller model: `MODEL_NAME=phi3:mini`
2. Reduce context: `TOP_K_RESULTS=3`
4. Add more RAM or swap space

### Vector Search Not Finding Results

**Rebuild vector database:**
```bash
./scripts/maintenance.sh
# Select option 7 (Rebuild Vector DB)

# Or manually:
rm -rf chroma_db
python -m src.data.vector_db
```

**Verify wiki data:**
```bash
ls -lh wiki_data/
# Should show wiki_docs_chunks.json (several MB)
```

### Ollama Connection Errors

**Check Ollama status:**
```bash
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve &
```

**Verify model is pulled:**
```bash
ollama list
# Should show your configured model

# Pull if missing
ollama pull phi3:mini
```

### Memory Issues on Raspberry Pi

**Enable swap:**
```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=4096
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

**Use minimal configuration:**
```env
MODEL_NAME=gemma2:2b
TOP_K_RESULTS=2
BATCH_SIZE=10
```

### Getting Help

1. Check logs: `docker-compose logs` or `tail -f logs/bot.log`
2. Run diagnostics: `./scripts/maintenance.sh` → Option 1
3. Test components: `python test_bot.py`
4. Check GitHub issues
5. Review Nextcloud Talk webhook documentation

---

## 🎉 Success!

Your Minecraft Wiki Bot should now be:
- ✅ Responding in Nextcloud Talk
- ✅ Answering Minecraft questions accurately
- ✅ Caching common queries for speed
- ✅ Running reliably in production

**Next Steps:**
- Monitor performance with `./scripts/maintenance.sh`
- Schedule regular wiki updates
- Configure automated backups
- Customize responses in `src/rag/pipeline.py`
- Add more features as needed

Happy crafting! 🎮⛏️

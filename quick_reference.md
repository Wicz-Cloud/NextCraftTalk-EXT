# 🚀 Minecraft Wiki Bot - Quick Reference

## 📦 One-Line Deployment

```bash
# Complete setup and deployment
git clone <repo> && cd minecraft-wiki-bot && chmod +x deploy-and-setup.sh && ./deploy-and-setup.sh docker production
```

## 🔧 Common Commands

### Docker Operations
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f minecraft_bot

# Restart bot
docker-compose restart minecraft_bot

# Rebuild image
docker-compose build --no-cache

# Check status
docker-compose ps
```

### Local Operations
```bash
# Activate environment
source venv/bin/activate

# Start bot
python nextcloud_bot.py

# Stop bot
kill $(cat bot.pid)

# View logs
tail -f logs/bot.log

# Run in background
nohup python nextcloud_bot.py > logs/bot.log 2>&1 &
```

### Maintenance
```bash
# Interactive maintenance menu
./maintenance.sh

# Quick commands
./maintenance.sh status       # Check status
./maintenance.sh backup       # Backup data
./maintenance.sh test         # Run tests
```

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/health

# Test query
curl -X POST "http://localhost:8000/test-query?query=diamond pickaxe"

# View stats
curl http://localhost:8000/stats

# Run test suite
python test_bot.py

# Simulate webhook
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"message":"test","token":"test","actor_id":"test"}'
```

## 📊 Monitoring

```bash
# System resources (Docker)
docker stats minecraft_bot

# Disk usage
du -sh wiki_data/ chroma_db/

# Log monitoring
journalctl -u minecraft-bot -f  # systemd
docker-compose logs -f --tail=50  # docker
tail -f logs/bot.log  # local
```

## 🔄 Updates & Maintenance

```bash
# Update wiki data
python wiki_scraper.py

# Rebuild vector database
python vector_db.py

# Update dependencies
pip install --upgrade -r requirements.txt

# Pull latest code
git pull && pip install -r requirements.txt

# Backup everything
tar -czf backup_$(date +%Y%m%d).tar.gz wiki_data chroma_db .env
```

## 🎯 Ollama Operations

```bash
# List models
ollama list

# Pull model
ollama pull phi3:mini
ollama pull gemma2:2b
ollama pull llama3:8b-instruct

# Remove model
ollama rm <model-name>

# Check Ollama status
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Test generation
ollama run phi3:mini "Hello, how are you?"
```

## 🗄️ Database Operations

```bash
# Vector database operations are handled automatically
# Use maintenance.sh for database management
```

## 🐛 Troubleshooting

```bash
# Check if bot is running
ps aux | grep nextcloud_bot
pgrep -f nextcloud_bot

# Check ports
netstat -tulpn | grep 8000
lsof -i :8000

# Test Nextcloud connectivity
curl -I https://your-nextcloud.com

# Check Docker logs for errors
docker-compose logs minecraft_bot | grep -i error

# Verify vector DB
python3 -c "from vector_db import MinecraftVectorDB; db=MinecraftVectorDB(); print(db.get_collection_stats())"

# Test RAG pipeline
python3 rag_pipeline.py

# Check Ollama connection
python3 -c "import requests; print(requests.get('http://localhost:11434/api/tags').json())"
```

## 📁 File Locations

```
minecraft-wiki-bot/
├── .env                      # Configuration (DO NOT COMMIT)
├── wiki_data/
│   ├── wiki_docs_full.json   # Complete wiki pages
│   └── wiki_docs_chunks.json # Chunked documents
├── chroma_db/                # Vector database
├── logs/
│   └── bot.log               # Application logs
└── backups/                  # Backup archives
```

## 🔐 Security Checklist

```bash
# Check .env permissions
chmod 600 .env

# Verify .env is in .gitignore
cat .gitignore | grep .env

# Check firewall (UFW)
sudo ufw status
sudo ufw allow 8000/tcp  # if needed

# SSL/TLS (with Let's Encrypt)
sudo certbot --nginx -d bot.yourdomain.com
```

## 🎮 Usage Examples in Nextcloud Talk

```
# Direct mention
@MinecraftBot How do I craft a diamond pickaxe?

# Natural language (bot detects keywords)
What's the recipe for a brewing stand?
How do I enchant items?
Tell me about golden apples
How to make a beacon?

# The bot responds to:
- craft/crafting questions
- recipe queries  
- "how do I" questions
- "how to make" questions
- Minecraft-related keywords
```

## 📈 Performance Tuning

### For Raspberry Pi (4-8GB RAM)
```env
MODEL_NAME=phi3:mini
TOP_K_RESULTS=3
BATCH_SIZE=25
MAX_WORKERS=2
```

### For Server (8-16GB RAM)
```env
MODEL_NAME=mistral:7b-instruct
TOP_K_RESULTS=5
BATCH_SIZE=50
MAX_WORKERS=4
```

### For High-End Server (16GB+ RAM)
```env
MODEL_NAME=llama3:8b-instruct
TOP_K_RESULTS=7
BATCH_SIZE=100
MAX_WORKERS=8
```

## 🚨 Emergency Recovery

```bash
# Bot crashed - restart quickly
docker-compose restart minecraft_bot

# or
kill $(cat bot.pid) && nohup python3 nextcloud_bot.py > logs/bot.log 2>&1 &

# Restore from backup
tar -xzf backups/backup_YYYYMMDD.tar.gz
docker-compose restart

# Reset everything (nuclear option)
docker-compose down
rm -rf chroma_db
python3 vector_db.py
docker-compose up -d
```

## 📞 Quick Diagnostics

```bash
# All-in-one health check
echo "=== Bot Status ===" && \
curl -s http://localhost:8000/health | python3 -m json.tool && \
echo "=== Ollama Status ===" && \
curl -s http://localhost:11434/api/tags | python3 -m json.tool && \
echo "=== Docker Status ===" && \
docker-compose ps && \
echo "=== Disk Usage ===" && \
df -h .
```

## 🔗 Important URLs

```
# Bot API
http://localhost:8000              # Root
http://localhost:8000/health       # Health check
http://localhost:8000/stats        # Statistics
http://localhost:8000/webhook      # Nextcloud webhook endpoint

# Ollama
http://localhost:11434             # Ollama API
http://localhost:11434/api/tags    # List models
```

## 💡 Tips & Best Practices

1. **Always backup before updates**
   ```bash
   ./maintenance.sh  # Option 3: Backup
   ```

2. **Update wiki data regularly**
   - Update wiki data monthly
   
3. **Watch memory usage**
   - Restart bot daily if memory grows
   - Use smaller model if swapping

4. **Log rotation**
   - Keep logs under 100MB
   - Archive old logs monthly

5. **Test after every change**
   ```bash
   python test_bot.py
   ```

## 📚 Documentation Quick Links

- Full README: `README.md`
- Deployment Guide: `DEPLOYMENT_GUIDE.md`
- Test Suite: `test_bot.py`
- Maintenance: `./maintenance.sh`

## 🆘 Common Issues & Fixes

| Issue | Quick Fix |
|-------|-----------|
| Bot not responding | `docker-compose restart minecraft_bot` |
| Slow responses | Check `MODEL_NAME` in .env, use smaller model |
| "Ollama not found" | `ollama serve &` |
| High memory usage | Restart bot, use `phi3:mini` |
| Vector search fails | `python3 vector_db.py` (rebuild) |
| Webhook 404 | Verify URL in Nextcloud settings |

## 🎓 Learning Resources

```bash
# Explore the code
cat wiki_scraper.py      # How wiki scraping works
cat vector_db.py         # How vector search works
cat rag_pipeline.py      # How RAG generation works
cat nextcloud_bot.py     # How webhook handling works

# Test components individually
python3 wiki_scraper.py  # Scrape wiki
python3 vector_db.py     # Build/test vector DB
python3 rag_pipeline.py  # Test RAG pipeline
```

---

**🎮 Happy Minecraft Botting! ⛏️**

For detailed information, see the full documentation in `README.md` and `DEPLOYMENT_GUIDE.md`.

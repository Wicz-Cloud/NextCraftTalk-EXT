#!/bin/bash
set -e

echo "================================================"
echo "Minecraft Wiki Bot Setup Script"
echo "================================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.11+${NC}"
    exit 1
fi

echo -e "${BLUE}1. Creating project structure...${NC}"
mkdir -p wiki_data
mkdir -p chroma_db
mkdir -p logs

echo -e "${BLUE}2. Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${BLUE}3. Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${BLUE}4. Setting up configuration...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file. Please edit it with your Nextcloud credentials.${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

echo -e "${BLUE}5. Checking for Docker and Docker Compose...${NC}"
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
else
    echo -e "${RED}⚠ Docker or Docker Compose not found. Install them for full deployment.${NC}"
fi

echo -e "${BLUE}6. Setting up Ollama...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama is installed${NC}"
    echo "Pulling recommended model (phi3:mini)..."
    ollama pull phi3:mini
else
    echo -e "${RED}⚠ Ollama not found. Install from https://ollama.ai${NC}"
    echo "Or use Docker Compose to run Ollama in a container"
fi

echo -e "${BLUE}7. Scraping Minecraft Wiki (this may take 10-30 minutes)...${NC}"
read -p "Do you want to scrape the wiki now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python wiki_scraper.py
    echo -e "${GREEN}✓ Wiki data scraped${NC}"
else
    echo -e "${BLUE}Skipping wiki scraping. Run 'python wiki_scraper.py' manually later.${NC}"
fi

echo -e "${BLUE}8. Building vector database...${NC}"
if [ -f "wiki_data/wiki_docs_chunks.json" ]; then
    python vector_db.py
    echo -e "${GREEN}✓ Vector database created${NC}"
else
    echo -e "${RED}⚠ Wiki data not found. Run wiki_scraper.py first.${NC}"
fi

echo -e "${BLUE}9. Seeding recipe cache...${NC}"
python cache_manager.py

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env with your Nextcloud credentials"
echo "2. Start the bot:"
echo "   - Local: python nextcloud_bot.py"
echo "   - Docker: docker-compose up -d"
echo ""
echo "3. Configure Nextcloud Talk webhook:"
echo "   - Go to Talk settings → Bots"
echo "   - Add webhook: http://your-server:8000/webhook"
echo "   - Set bot name: MinecraftBot"
echo ""
echo "4. Test the bot:"
echo "   curl http://localhost:8000/health"
echo ""
echo "Documentation: See README.md for full details"

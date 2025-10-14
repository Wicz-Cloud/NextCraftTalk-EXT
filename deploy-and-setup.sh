#!/bin/bash
set -e

# Combined Setup and Deployment Script for Minecraft Wiki Bot
# This script handles both initial setup and deployment in a unified workflow
# Supports: Standard server, Raspberry Pi, Docker deployments

echo "================================================"
echo "Minecraft Wiki Bot - Setup & Deployment"
echo "================================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
DEPLOY_TYPE=${1:-"docker"}  # docker, local, or pi
ENVIRONMENT=${2:-"production"}

# Global flags
NEEDS_SETUP=false

# ============================================================
# SETUP FUNCTIONS (from setup.sh)
# ============================================================

check_python() {
    echo -e "${BLUE}Checking Python installation...${NC}"
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 is not installed. Please install Python 3.11+${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python 3 is installed${NC}"
}

create_project_structure() {
    echo -e "${BLUE}Creating project structure...${NC}"
    mkdir -p wiki_data
    mkdir -p chroma_db
    mkdir -p logs
    mkdir -p backups
    echo -e "${GREEN}✓ Project directories created${NC}"
}

setup_virtual_environment() {
    echo -e "${BLUE}Setting up virtual environment...${NC}"
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    else
        echo -e "${GREEN}✓ Virtual environment already exists${NC}"
    fi
}

install_dependencies() {
    echo -e "${BLUE}Installing Python dependencies...${NC}"
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
}

setup_env_file() {
    echo -e "${BLUE}Setting up configuration...${NC}"
    if [ ! -f .env ]; then
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
        echo -e "${YELLOW}⚠ Please edit .env with your Nextcloud credentials before deploying${NC}"
        return 1
    else
        echo -e "${GREEN}✓ .env file already exists${NC}"
        return 0
    fi
}

check_docker_compose() {
    echo -e "${BLUE}Checking for Docker and Docker Compose...${NC}"
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
        return 0
    else
        echo -e "${RED}⚠ Docker or Docker Compose not found${NC}"
        if [ "$DEPLOY_TYPE" = "docker" ]; then
            echo -e "${RED}Docker deployment requires Docker and Docker Compose${NC}"
            exit 1
        fi
        return 1
    fi
}

setup_ollama() {
    echo -e "${BLUE}Setting up Ollama...${NC}"
    if command -v ollama &> /dev/null; then
        echo -e "${GREEN}✓ Ollama is installed${NC}"
        echo "Pulling recommended model (phi3:mini)..."
        ollama pull phi3:mini
        echo -e "${GREEN}✓ Model pulled${NC}"
    else
        echo -e "${YELLOW}⚠ Ollama not found${NC}"
        if [ "$DEPLOY_TYPE" != "docker" ]; then
            echo -e "${RED}Local deployment requires Ollama. Install from https://ollama.ai${NC}"
            echo "Or use Docker deployment (./deploy-and-setup.sh docker)"
            exit 1
        else
            echo -e "${BLUE}Ollama will run in Docker container${NC}"
        fi
    fi
}

scrape_wiki_data() {
    echo -e "${BLUE}Scraping Minecraft Wiki...${NC}"
    echo -e "${YELLOW}This may take 10-30 minutes${NC}"
    
    if [ -f "wiki_data/wiki_docs_chunks.json" ]; then
        echo -e "${YELLOW}Wiki data already exists. Re-scrape? (y/n)${NC}"
        read -r response
        if [ "$response" != "y" ]; then
            echo -e "${BLUE}Skipping wiki scraping${NC}"
            return 0
        fi
    fi
    
    echo -e "${YELLOW}Do you want to scrape the wiki now? (y/n)${NC}"
    read -r response
    if [ "$response" = "y" ]; then
        source venv/bin/activate
        python wiki_scraper.py
        echo -e "${GREEN}✓ Wiki data scraped${NC}"
    else
        echo -e "${BLUE}Skipping wiki scraping. Run 'python wiki_scraper.py' manually later${NC}"
        return 1
    fi
}

build_vector_database() {
    echo -e "${BLUE}Building vector database...${NC}"
    if [ ! -f "wiki_data/wiki_docs_chunks.json" ]; then
        echo -e "${RED}⚠ Wiki data not found. Run wiki scraper first${NC}"
        return 1
    fi
    
    source venv/bin/activate
    python vector_db.py
    echo -e "${GREEN}✓ Vector database created${NC}"
}

seed_cache() {
    echo -e "${BLUE}Seeding recipe cache...${NC}"
    source venv/bin/activate
    python cache_manager.py
    echo -e "${GREEN}✓ Recipe cache seeded${NC}"
}

run_initial_setup() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Running Initial Setup${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    check_python
    create_project_structure
    setup_virtual_environment
    install_dependencies
    
    local env_configured
    setup_env_file
    env_configured=$?
    
    check_docker_compose
    
    if [ "$DEPLOY_TYPE" = "local" ]; then
        setup_ollama
    fi
    
    scrape_wiki_data
    build_vector_database
    seed_cache
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Initial Setup Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    if [ $env_configured -ne 0 ]; then
        echo -e "${YELLOW}⚠ Please edit .env file with your Nextcloud credentials${NC}"
        echo -e "${YELLOW}Then run this script again to deploy${NC}"
        exit 0
    fi
}

# ============================================================
# DEPLOYMENT FUNCTIONS (from deploy.sh)
# ============================================================

check_requirements() {
    echo -e "${BLUE}Checking deployment requirements...${NC}"
    
    # Check Docker
    if [ "$DEPLOY_TYPE" = "docker" ]; then
        if ! command -v docker &> /dev/null; then
            echo -e "${RED}Docker not found. Install Docker first.${NC}"
            exit 1
        fi
        if ! command -v docker-compose &> /dev/null; then
            echo -e "${RED}Docker Compose not found.${NC}"
            exit 1
        fi
    fi
    
    # Check .env file
    if [ ! -f .env ]; then
        echo -e "${RED}.env file not found.${NC}"
        return 1
    fi
    
    # Verify critical env vars
    source .env
    if [ -z "$NEXTCLOUD_URL" ] || [ -z "$NEXTCLOUD_BOT_TOKEN" ]; then
        echo -e "${RED}Missing Nextcloud configuration in .env${NC}"
        echo -e "${YELLOW}Please edit .env with your credentials${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ Requirements check passed${NC}"
    return 0
}

backup_data() {
    echo -e "${BLUE}Creating backup...${NC}"
    
    BACKUP_DIR="backups/backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup databases and data
    [ -d "chroma_db" ] && cp -r chroma_db "$BACKUP_DIR/"
    [ -f "recipe_cache.db" ] && cp recipe_cache.db "$BACKUP_DIR/"
    [ -d "wiki_data" ] && cp -r wiki_data "$BACKUP_DIR/"
    
    echo -e "${GREEN}✓ Backup created: $BACKUP_DIR${NC}"
}

deploy_docker() {
    echo -e "${BLUE}Deploying with Docker Compose...${NC}"
    
    # Pull latest images
    echo "Pulling latest images..."
    docker-compose pull
    
    # Build custom image
    echo "Building bot image..."
    docker-compose build
    
    # Start services
    echo "Starting services..."
    docker-compose up -d
    
    # Wait for services to be healthy
    echo "Waiting for services to start..."
    sleep 10
    
    # Check health
    source .env 2>/dev/null || true
    BOT_PORT=${BOT_PORT:-8000}
    for i in {1..30}; do
        if curl -f http://localhost:${BOT_PORT}/health &> /dev/null; then
            echo -e "${GREEN}✓ Bot is healthy!${NC}"
            break
        fi
        echo "Waiting for bot to be ready... ($i/30)"
        sleep 2
    done
    
    # Show logs
    echo -e "\n${BLUE}Recent logs:${NC}"
    docker-compose logs --tail=20 minecraft_bot
}

deploy_local() {
    echo -e "${BLUE}Deploying locally...${NC}"
    
    # Activate virtual environment
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    # Install/update dependencies
    echo "Installing dependencies..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    # Load env vars
    source .env
    OLLAMA_PORT=${OLLAMA_PORT:-11434}
    BOT_PORT=${BOT_PORT:-8000}
    
    # Check if Ollama is running
    if ! curl -f http://localhost:${OLLAMA_PORT}/api/tags &> /dev/null; then
        echo -e "${YELLOW}⚠ Ollama not detected. Starting Ollama...${NC}"
        ollama serve &
        OLLAMA_PID=$!
        sleep 5
    fi
    
    # Start bot
    echo "Starting bot service..."
    nohup python nextcloud_bot.py > logs/bot.log 2>&1 &
    BOT_PID=$!
    echo $BOT_PID > bot.pid
    
    sleep 5
    
    # Check health
    if curl -f http://localhost:${BOT_PORT}/health &> /dev/null; then
        echo -e "${GREEN}✓ Bot started successfully (PID: $BOT_PID)${NC}"
    else
        echo -e "${RED}✗ Bot failed to start. Check logs/bot.log${NC}"
        exit 1
    fi
}

deploy_raspberry_pi() {
    echo -e "${BLUE}Deploying for Raspberry Pi...${NC}"
    
    # Check if running on ARM
    if [ "$(uname -m)" != "aarch64" ] && [ "$(uname -m)" != "armv7l" ]; then
        echo -e "${YELLOW}⚠ Not running on ARM architecture. Continue anyway? (y/n)${NC}"
        read -r response
        if [ "$response" != "y" ]; then
            exit 0
        fi
    fi
    
    # Optimize for Pi
    echo "Configuring for Raspberry Pi..."
    
    # Update .env for Pi optimizations
    if ! grep -q "MAX_WORKERS" .env; then
        echo -e "\n# Raspberry Pi Optimizations" >> .env
        echo "MAX_WORKERS=2" >> .env
        echo "BATCH_SIZE=25" >> .env
        echo "TOP_K_RESULTS=3" >> .env
    fi
    
    # Ensure using lightweight model
    sed -i 's/MODEL_NAME=.*/MODEL_NAME=phi3:mini/' .env 2>/dev/null || \
        echo "MODEL_NAME=phi3:mini" >> .env
    
    # Deploy using Docker (lighter on resources)
    deploy_docker
    
    echo -e "${YELLOW}⚠ Monitor temperature: vcgencmd measure_temp${NC}"
}

setup_systemd_service() {
    echo -e "${BLUE}Setting up systemd service...${NC}"
    
    SERVICE_FILE="/etc/systemd/system/minecraft-bot.service"
    
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Minecraft Wiki Bot for Nextcloud Talk
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=$USER

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable minecraft-bot.service
    
    echo -e "${GREEN}✓ Systemd service installed${NC}"
    echo "  Start: sudo systemctl start minecraft-bot"
    echo "  Stop:  sudo systemctl stop minecraft-bot"
    echo "  Status: sudo systemctl status minecraft-bot"
}

run_tests() {
    echo -e "${BLUE}Running tests...${NC}"
    
    if [ -f "test_bot.py" ]; then
        python test_bot.py
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ All tests passed${NC}"
        else
            echo -e "${RED}✗ Some tests failed${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠ Test file not found, skipping tests${NC}"
    fi
}

show_status() {
    echo -e "\n${BLUE}=== Deployment Status ===${NC}"
    
    source .env 2>/dev/null || true
    BOT_PORT=${BOT_PORT:-8000}
    
    if [ "$DEPLOY_TYPE" = "docker" ]; then
        docker-compose ps
        echo -e "\n${BLUE}Health Check:${NC}"
        curl -s http://localhost:${BOT_PORT}/health | python -m json.tool || echo "Service not responding"
    else
        if [ -f "bot.pid" ]; then
            PID=$(cat bot.pid)
            if ps -p $PID > /dev/null; then
                echo -e "${GREEN}✓ Bot running (PID: $PID)${NC}"
            else
                echo -e "${RED}✗ Bot not running${NC}"
            fi
        fi
    fi
    
    echo -e "\n${BLUE}Statistics:${NC}"
    curl -s http://localhost:${BOT_PORT}/stats | python -m json.tool || echo "Stats not available"
}

# ============================================================
# MAIN WORKFLOW
# ============================================================

detect_setup_needed() {
    # Check if initial setup is needed
    if [ ! -d "venv" ] || [ ! -f ".env" ] || [ ! -d "chroma_db" ] || [ ! -f "wiki_data/wiki_docs_chunks.json" ]; then
        NEEDS_SETUP=true
    else
        NEEDS_SETUP=false
    fi
}

show_usage() {
    echo "Usage: ./deploy-and-setup.sh [deployment-type] [environment]"
    echo ""
    echo "Deployment Types:"
    echo "  docker           - Deploy using Docker Compose (default)"
    echo "  local            - Deploy locally with Python virtual environment"
    echo "  pi|raspberry-pi  - Deploy on Raspberry Pi with optimizations"
    echo ""
    echo "Environments:"
    echo "  production       - Production mode with backups and tests (default)"
    echo "  development      - Development mode (skips backups and tests)"
    echo ""
    echo "Examples:"
    echo "  ./deploy-and-setup.sh docker production"
    echo "  ./deploy-and-setup.sh local development"
    echo "  ./deploy-and-setup.sh pi production"
    echo ""
    echo "This script will:"
    echo "  1. Detect if initial setup is needed"
    echo "  2. Run setup steps if required (create venv, install deps, scrape wiki, etc.)"
    echo "  3. Deploy the bot according to the specified type"
    echo "  4. Show deployment status and next steps"
}

main() {
    echo "Deployment Type: $DEPLOY_TYPE"
    echo "Environment: $ENVIRONMENT"
    echo ""
    
    # Show usage if help is requested
    if [ "$DEPLOY_TYPE" = "-h" ] || [ "$DEPLOY_TYPE" = "--help" ]; then
        show_usage
        exit 0
    fi
    
    # Validate deployment type
    case $DEPLOY_TYPE in
        docker|local|pi|raspberry-pi)
            ;;
        *)
            echo -e "${RED}Unknown deployment type: $DEPLOY_TYPE${NC}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
    
    # Detect if setup is needed
    detect_setup_needed
    
    if [ "$NEEDS_SETUP" = true ]; then
        echo -e "${YELLOW}Initial setup required${NC}"
        run_initial_setup
    else
        echo -e "${GREEN}✓ Setup already completed${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Starting Deployment${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Pre-deployment checks
    if ! check_requirements; then
        echo -e "${RED}Requirements check failed. Please fix the issues above.${NC}"
        exit 1
    fi
    
    # Backup existing data
    if [ "$ENVIRONMENT" = "production" ]; then
        backup_data
    fi
    
    # Run tests
    if [ "$ENVIRONMENT" = "production" ]; then
        run_tests
    fi
    
    # Deploy based on type
    case $DEPLOY_TYPE in
        docker)
            deploy_docker
            ;;
        local)
            deploy_local
            ;;
        pi|raspberry-pi)
            deploy_raspberry_pi
            ;;
    esac
    
    # Setup systemd service (optional)
    if [ "$ENVIRONMENT" = "production" ] && [ "$DEPLOY_TYPE" = "docker" ]; then
        echo -e "\n${YELLOW}Setup systemd service? (y/n)${NC}"
        read -r response
        if [ "$response" = "y" ]; then
            setup_systemd_service
        fi
    fi
    
    # Show final status
    show_status
    
    source .env 2>/dev/null || true
    BOT_PORT=${BOT_PORT:-8000}
    NEXTCLOUD_URL=${NEXTCLOUD_URL:-"your-nextcloud-url"}
    
    echo -e "\n${GREEN}================================================${NC}"
    echo -e "${GREEN}Setup and Deployment Complete!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo -e "\nNext steps:"
    echo "1. Test the bot: curl http://localhost:${BOT_PORT}/health"
    echo "2. Configure Nextcloud webhook: $NEXTCLOUD_URL"
    echo "3. Monitor logs: docker-compose logs -f (or tail -f logs/bot.log)"
    echo "4. Test in Talk: @MinecraftBot How do I craft a diamond pickaxe?"
    echo ""
    echo "For maintenance tasks, use: ./maintenance.sh"
}

# Run main
main

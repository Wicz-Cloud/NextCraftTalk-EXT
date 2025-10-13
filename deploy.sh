#!/bin/bash
set -e

# Production Deployment Script for Minecraft Wiki Bot
# Supports: Standard server, Raspberry Pi, Docker deployments

echo "================================================"
echo "Minecraft Wiki Bot - Production Deployment"
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

# Functions
check_requirements() {
    echo -e "${BLUE}Checking requirements...${NC}"
    
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
        echo -e "${RED}.env file not found. Copy .env.example and configure it.${NC}"
        exit 1
    fi
    
    # Verify critical env vars
    source .env
    if [ -z "$NEXTCLOUD_URL" ] || [ -z "$NEXTCLOUD_BOT_TOKEN" ]; then
        echo -e "${RED}Missing Nextcloud configuration in .env${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Requirements check passed${NC}"
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

# Main deployment flow
main() {
    echo "Deployment Type: $DEPLOY_TYPE"
    echo "Environment: $ENVIRONMENT"
    echo ""
    
    # Pre-deployment checks
    check_requirements
    
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
        *)
            echo -e "${RED}Unknown deployment type: $DEPLOY_TYPE${NC}"
            echo "Usage: ./deploy.sh [docker|local|pi] [production|development]"
            exit 1
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
    
    echo -e "\n${GREEN}================================================${NC}"
    echo -e "${GREEN}Deployment Complete!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo -e "\nNext steps:"
    echo "1. Test the bot: curl http://localhost:${BOT_PORT}/health"
    echo "2. Configure Nextcloud webhook: $NEXTCLOUD_URL"
    echo "3. Monitor logs: docker-compose logs -f (or tail -f logs/bot.log)"
    echo "4. Test in Talk: @MinecraftBot How do I craft a diamond pickaxe?"
}

# Run main
main

#!/bin/bash

# Maintenance and Monitoring Script for Minecraft Wiki Bot
# Provides tools for updates, backups, monitoring, and troubleshooting

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

show_menu() {
    echo "================================================"
    echo "   Minecraft Wiki Bot - Maintenance Menu"
    echo "================================================"
    echo ""
    echo "1) Status & Health Check"
    echo "2) View Logs"
    echo "3) Backup Data"
    echo "4) Restore from Backup"
    echo "5) Update Wiki Data"
    echo "6) Rebuild Vector DB"
    echo "7) Update Bot (pull latest)"
    echo "8) Performance Report"
    echo "9) Test Bot"
    echo "10) Restart Services"
    echo "0) Exit"
    echo ""
    echo -n "Select option: "
}

status_check() {
    echo -e "${BLUE}=== System Status ===${NC}"

    # Check if Docker or local
    if docker ps | grep -q minecraft_bot; then
        echo -e "${GREEN}✓ Docker deployment detected${NC}"
        echo ""
        docker-compose ps
        echo ""

        # Container health
        echo "Container Health:"
        docker inspect minecraft_bot --format='{{.State.Health.Status}}' 2>/dev/null || echo "No healthcheck"

    elif [ -f "bot.pid" ] && ps -p $(cat bot.pid) > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Local deployment - Bot running${NC}"
        echo "PID: $(cat bot.pid)"
    else
        echo -e "${RED}✗ Bot not running${NC}"
        return 1
    fi

    echo ""
    echo -e "${BLUE}=== API Health ===${NC}"
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        curl -s http://localhost:8000/health | python3 -m json.tool
    else
        echo -e "${RED}✗ API not responding${NC}"
    fi

    echo ""
    echo -e "${BLUE}=== Ollama Status ===${NC}"
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Ollama is running${NC}"
        echo "Available models:"
        curl -s http://localhost:11434/api/tags | python3 -c "import sys, json; [print(f\"  - {m['name']}\") for m in json.load(sys.stdin)['models']]"
    else
        echo -e "${RED}✗ Ollama not responding${NC}"
    fi

    echo ""
    echo -e "${BLUE}=== Database Status ===${NC}"

    if [ -d "chroma_db" ]; then
        SIZE=$(du -sh chroma_db | cut -f1)
        echo "Vector DB: $SIZE"
    fi

    echo ""
    echo -e "${BLUE}=== Disk Usage ===${NC}"
    df -h . | tail -1
}

view_logs() {
    echo -e "${BLUE}=== Recent Logs ===${NC}"
    echo ""

    if docker ps | grep -q minecraft_bot; then
        echo "Docker logs (last 50 lines):"
        docker-compose logs --tail=50 minecraft_bot
    elif [ -f "logs/bot.log" ]; then
        echo "Local logs (last 50 lines):"
        tail -50 logs/bot.log
    else
        echo -e "${RED}No logs found${NC}"
    fi

    echo ""
    echo "Press Enter to return to menu..."
    read
}

backup_data() {
    echo -e "${BLUE}Creating backup...${NC}"

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_DIR="backups/backup_$TIMESTAMP"
    mkdir -p "$BACKUP_DIR"

    # Backup databases
    # Backup vector database
    if [ -d "chroma_db" ]; then
        cp -r chroma_db "$BACKUP_DIR/"
        echo "✓ Vector database backed up"
    fi

    # Backup wiki data
    if [ -d "wiki_data" ]; then
        cp -r wiki_data "$BACKUP_DIR/"
        echo "✓ Wiki data backed up"
    fi

    # Backup configuration
    if [ -f ".env" ]; then
        cp .env "$BACKUP_DIR/env.backup"
        echo "✓ Configuration backed up"
    fi

    # Create archive
    tar -czf "$BACKUP_DIR.tar.gz" -C backups "backup_$TIMESTAMP"
    rm -rf "$BACKUP_DIR"

    echo -e "${GREEN}✓ Backup created: $BACKUP_DIR.tar.gz${NC}"
    du -h "$BACKUP_DIR.tar.gz"
}

restore_backup() {
    echo -e "${BLUE}Available backups:${NC}"
    ls -lh backups/*.tar.gz 2>/dev/null || echo "No backups found"

    echo ""
    echo -n "Enter backup filename to restore (or 'cancel'): "
    read BACKUP_FILE

    if [ "$BACKUP_FILE" = "cancel" ]; then
        return
    fi

    if [ ! -f "backups/$BACKUP_FILE" ]; then
        echo -e "${RED}Backup file not found${NC}"
        return
    fi

    echo -e "${YELLOW}⚠ This will overwrite current data. Continue? (yes/no)${NC}"
    read CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        echo "Cancelled"
        return
    fi

    # Extract backup
    tar -xzf "backups/$BACKUP_FILE" -C backups/
    BACKUP_DIR=$(basename "$BACKUP_FILE" .tar.gz)

    # Restore files
    [ -d "backups/$BACKUP_DIR/chroma_db" ] && cp -r "backups/$BACKUP_DIR/chroma_db" .
    [ -d "backups/$BACKUP_DIR/wiki_data" ] && cp -r "backups/$BACKUP_DIR/wiki_data" .

    rm -rf "backups/$BACKUP_DIR"

    echo -e "${GREEN}✓ Backup restored. Restart bot to apply changes.${NC}"
}

update_wiki_data() {
    echo -e "${BLUE}Updating Wiki Data...${NC}"
    echo "This will re-scrape minecraft.wiki (may take 10-30 minutes)"
    echo -n "Continue? (yes/no): "
    read CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        return
    fi

    # Backup current data first
    backup_data

    # Run scraper
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

    python3 wiki_scraper.py

    echo -e "${GREEN}✓ Wiki data updated${NC}"
    echo -e "${YELLOW}⚠ Remember to rebuild vector DB (option 7)${NC}"
}

rebuild_vector_db() {
    echo -e "${BLUE}Rebuilding Vector Database...${NC}"
    echo -e "${YELLOW}This will delete and recreate the vector database${NC}"
    echo -n "Continue? (yes/no): "
    read CONFIRM

    if [ "$CONFIRM" != "yes" ]; then
        return
    fi

    # Backup first
    backup_data

    # Remove old vector DB
    rm -rf chroma_db

    # Rebuild
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi

    python3 vector_db.py

    echo -e "${GREEN}✓ Vector database rebuilt${NC}"
    echo -e "${YELLOW}⚠ Restart bot to use new database${NC}"
}

update_bot() {
    echo -e "${BLUE}Updating Bot Code...${NC}"

    if [ -d ".git" ]; then
        echo "Pulling latest changes from git..."
        git pull

        echo "Updating dependencies..."
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        pip install -r requirements.txt

        echo -e "${GREEN}✓ Bot updated${NC}"
        echo -e "${YELLOW}⚠ Restart bot to apply changes${NC}"
    else
        echo -e "${RED}Not a git repository. Manual update required.${NC}"
    fi
}

performance_report() {
    echo -e "${BLUE}=== Performance Report ===${NC}"

    # Get stats from API
    if curl -s http://localhost:8000/stats > /dev/null 2>&1; then
        echo ""
        echo "Bot Statistics:"
        curl -s http://localhost:8000/stats | python3 -m json.tool
    fi

    echo ""
    echo -e "${BLUE}=== System Resources ===${NC}"

    if docker ps | grep -q minecraft_bot; then
        echo "Docker Container Stats:"
        docker stats minecraft_bot --no-stream
    else
        echo "System Memory:"
        free -h
        echo ""
        echo "CPU Usage:"
        top -bn1 | head -5
    fi

    echo ""
    echo -e "${BLUE}=== Database Stats ===${NC}"

    echo ""
    echo "Press Enter to return to menu..."
    read
}

test_bot() {
    echo -e "${BLUE}Testing Bot...${NC}"
    echo ""

    TEST_QUERIES=(
        "How do I craft a diamond pickaxe?"
        "What is the recipe for a brewing stand?"
        "How do I make a golden apple?"
    )

    for query in "${TEST_QUERIES[@]}"; do
        echo -e "${YELLOW}Query:${NC} $query"

        RESPONSE=$(curl -s -X POST "http://localhost:8000/test-query?query=$query")

        if [ $? -eq 0 ]; then
            echo "$RESPONSE" | python3 -m json.tool | head -20
            echo -e "${GREEN}✓ Success${NC}"
        else
            echo -e "${RED}✗ Failed${NC}"
        fi

        echo ""
        sleep 1
    done

    echo "Press Enter to return to menu..."
    read
}

restart_services() {
    echo -e "${BLUE}Restarting Services...${NC}"

    if docker ps | grep -q minecraft_bot; then
        echo "Restarting Docker services..."
        docker-compose restart
        sleep 5
        echo -e "${GREEN}✓ Services restarted${NC}"
    elif [ -f "bot.pid" ]; then
        echo "Stopping bot..."
        kill $(cat bot.pid) 2>/dev/null || true
        sleep 2

        echo "Starting bot..."
        nohup python3 nextcloud_bot.py > logs/bot.log 2>&1 &
        echo $! > bot.pid
        sleep 3

        echo -e "${GREEN}✓ Bot restarted${NC}"
    else
        echo -e "${RED}No running instance found${NC}"
    fi

    # Verify health
    sleep 3
    if curl -s http://localhost:8000/health > /dev/null; then
        echo -e "${GREEN}✓ Bot is healthy${NC}"
    else
        echo -e "${RED}✗ Bot health check failed${NC}"
    fi
}

# Main loop
while true; do
    clear
    show_menu
    read OPTION

    case $OPTION in
        1) status_check; echo ""; echo "Press Enter to continue..."; read ;;
        2) view_logs ;;
        3) backup_data; echo ""; echo "Press Enter to continue..."; read ;;
        4) restore_backup; echo ""; echo "Press Enter to continue..."; read ;;
        5) update_wiki_data; echo ""; echo "Press Enter to continue..."; read ;;
        6) rebuild_vector_db; echo ""; echo "Press Enter to continue..."; read ;;
        7) update_bot; echo ""; echo "Press Enter to continue..."; read ;;
        8) performance_report ;;
        9) test_bot ;;
        10) restart_services; echo ""; echo "Press Enter to continue..."; read ;;
        0) echo "Exiting..."; exit 0 ;;
        *) echo -e "${RED}Invalid option${NC}"; sleep 1 ;;
    esac
done

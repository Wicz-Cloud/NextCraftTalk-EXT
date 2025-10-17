#!/bin/bash

# Minecraft Bot Deployment Script with Conflict Checks
# This script provides comprehensive deployment with safety checks

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEPLOY_TYPE="${1:-docker}"
ENVIRONMENT="${2:-production}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Configuration
REQUIRED_PORTS=("8000" "11434")  # Bot port, Ollama port
CONTAINER_NAMES=("minecraft_bot" "ollama")
OLLAMA_MODEL="phi3:mini"

# Load environment variables from .env file if it exists
if [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env"
fi

# Network configuration (configurable via environment)
NETWORK_NAME="${NETWORK_NAME:-nextcloud-aio}"

# Logging
LOG_FILE="$PROJECT_DIR/logs/deploy_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}ERROR: $*${NC}" >&2
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: $*" >> "$LOG_FILE"
}

success() {
    echo -e "${GREEN}✓ $*${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $*${NC}"
}

info() {
    echo -e "${BLUE}ℹ $*${NC}"
}

# ============================================================
# CONFLICT DETECTION FUNCTIONS
# ============================================================

check_port_conflicts() {
    log "Checking for port conflicts..."

    local conflicts_found=false

    for port in "${REQUIRED_PORTS[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            error "Port $port is already in use"
            lsof -Pi :$port -sTCP:LISTEN
            conflicts_found=true
        else
            success "Port $port is available"
        fi
    done

    if [ "$conflicts_found" = true ]; then
        error "Port conflicts detected. Please free up the conflicting ports or change them in docker-compose.yml"
        return 1
    fi

    return 0
}

check_container_conflicts() {
    log "Checking for container name conflicts..."

    local conflicts_found=false

    for container in "${CONTAINER_NAMES[@]}"; do
        if docker ps -a --format "table {{.Names}}" | grep -q "^${container}$"; then
            warning "Container '$container' already exists"

            # Show container status
            docker ps -a --filter "name=^${container}$" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

            echo -e "${YELLOW}Options:${NC}"
            echo "1. Remove existing container and continue"
            echo "2. Rename container in docker-compose.yml"
            echo "3. Cancel deployment"
            read -p "Choose option (1-3): " choice

            case $choice in
                1)
                    log "Removing existing container: $container"
                    docker rm -f "$container" || true
                    success "Container $container removed"
                    ;;
                2)
                    error "Please rename the container in docker-compose.yml and run again"
                    return 1
                    ;;
                3)
                    log "Deployment cancelled by user"
                    exit 0
                    ;;
                *)
                    error "Invalid choice"
                    return 1
                    ;;
            esac
        else
            success "Container name '$container' is available"
        fi
    done

    return 0
}

check_network_conflicts() {
    log "Checking for network conflicts..."

    if docker network ls --format "{{.Name}}" | grep -q "^${NETWORK_NAME}$"; then
        success "Network '$NETWORK_NAME' exists"
    else
        warning "Network '$NETWORK_NAME' does not exist"

        echo -e "${YELLOW}Options:${NC}"
        echo "1. Create the network automatically"
        echo "2. Use a different network name in docker-compose.yml"
        echo "3. Cancel deployment"
        read -p "Choose option (1-3): " choice

        case $choice in
            1)
                log "Creating network: $NETWORK_NAME"
                docker network create "$NETWORK_NAME" || {
                    error "Failed to create network $NETWORK_NAME"
                    return 1
                }
                success "Network $NETWORK_NAME created"
                ;;
            2)
                error "Please update docker-compose.yml with the correct network name and run again"
                return 1
                ;;
            3)
                log "Deployment cancelled by user"
                exit 0
                ;;
            *)
                error "Invalid choice"
                return 1
                ;;
        esac
    fi

    return 0
}

check_docker_resources() {
    log "Checking Docker resources..."

    # Check available disk space
    local available_space
    available_space=$(docker system df --format "{{.Size}}" 2>/dev/null | tail -1 | sed 's/GB//')

    if [ -n "$available_space" ] && [ "${available_space%.*}" -lt 5 ]; then
        warning "Low disk space: ${available_space}GB available. At least 5GB recommended."
    fi

    # Check Docker version
    local docker_version
    docker_version=$(docker --version | sed 's/Docker version //' | cut -d. -f1)
    if [ "$docker_version" -lt 20 ]; then
        warning "Docker version $docker_version detected. Version 20+ recommended."
    fi

    success "Docker resource check completed"
}

# ============================================================
# DEPLOYMENT FUNCTIONS
# ============================================================

backup_existing_deployment() {
    log "Creating backup of existing deployment..."

    local backup_dir="$PROJECT_DIR/backups/pre_deploy_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    # Backup docker-compose state
    if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
        cp "$PROJECT_DIR/docker-compose.yml" "$backup_dir/"
    fi

    # Backup environment file
    if [ -f "$PROJECT_DIR/.env" ]; then
        cp "$PROJECT_DIR/.env" "$backup_dir/"
    fi

    # Backup data volumes if containers exist
    for container in "${CONTAINER_NAMES[@]}"; do
        if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
            log "Backing up data for container: $container"
            docker run --rm -v "${container}_data:/data" -v "$backup_dir:/backup" alpine tar czf "/backup/${container}_data.tar.gz" -C / data 2>/dev/null || true
        fi
    done

    success "Backup created: $backup_dir"
    echo "$backup_dir"
}

rollback_deployment() {
    local backup_dir="$1"

    error "Deployment failed. Starting rollback..."

    # Stop and remove containers
    cd "$PROJECT_DIR"
    docker-compose down --remove-orphans 2>/dev/null || true

    # Restore from backup if available
    if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
        log "Restoring from backup: $backup_dir"

        if [ -f "$backup_dir/docker-compose.yml" ]; then
            cp "$backup_dir/docker-compose.yml" "$PROJECT_DIR/"
        fi

        if [ -f "$backup_dir/.env" ]; then
            cp "$backup_dir/.env" "$PROJECT_DIR/"
        fi

        # Attempt to restore containers
        docker-compose up -d 2>/dev/null || true
    fi

    error "Rollback completed. Please check the logs and try again."
}

deploy_containers() {
    log "Starting container deployment..."

    cd "$PROJECT_DIR"

    # Pull base images
    log "Pulling base images..."
    docker-compose pull

    # Build custom images
    log "Building custom images..."
    docker-compose build --no-cache

    # Start containers
    log "Starting containers..."
    docker-compose up -d

    success "Containers started"
}

setup_ollama_model() {
    log "Setting up Ollama model: $OLLAMA_MODEL"

    local max_attempts=5
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        log "Attempt $attempt/$max_attempts: Pulling model $OLLAMA_MODEL"

        if docker-compose exec -T ollama ollama pull "$OLLAMA_MODEL"; then
            success "Model $OLLAMA_MODEL pulled successfully"
            return 0
        else
            warning "Failed to pull model (attempt $attempt/$max_attempts)"
            sleep 5
            ((attempt++))
        fi
    done

    error "Failed to pull Ollama model after $max_attempts attempts"
    return 1
}

wait_for_services() {
    log "Waiting for services to be ready..."

    local max_wait=120  # 2 minutes
    local wait_time=0

    # Load environment variables
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
    fi

    local bot_port=${BOT_PORT:-8000}
    local ollama_port=${OLLAMA_PORT:-11434}

    # Wait for Ollama
    log "Waiting for Ollama service..."
    while [ $wait_time -lt $max_wait ]; do
        if curl -f "http://localhost:$ollama_port/api/tags" >/dev/null 2>&1; then
            success "Ollama service is ready"
            break
        fi
        sleep 2
        ((wait_time += 2))
    done

    if [ $wait_time -ge $max_wait ]; then
        error "Ollama service failed to start within ${max_wait}s"
        return 1
    fi

    # Wait for bot
    log "Waiting for bot service..."
    wait_time=0
    while [ $wait_time -lt $max_wait ]; do
        if curl -f "http://localhost:$bot_port/health" >/dev/null 2>&1; then
            success "Bot service is ready"
            break
        fi
        sleep 2
        ((wait_time += 2))
    done

    if [ $wait_time -ge $max_wait ]; then
        error "Bot service failed to start within ${max_wait}s"
        return 1
    fi

    return 0
}

run_health_checks() {
    log "Running comprehensive health checks..."

    # Load environment variables
    if [ -f "$PROJECT_DIR/.env" ]; then
        source "$PROJECT_DIR/.env"
    fi

    local bot_port=${BOT_PORT:-8000}
    local ollama_port=${OLLAMA_PORT:-11434}

    # Check bot health
    log "Checking bot health..."
    local bot_health
    bot_health=$(curl -s "http://localhost:$bot_port/health" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unhealthy")

    if [ "$bot_health" = "healthy" ]; then
        success "Bot health check passed"
    else
        error "Bot health check failed: $bot_health"
        return 1
    fi

    # Check Ollama models
    log "Checking Ollama models..."
    local models
    models=$(curl -s "http://localhost:$ollama_port/api/tags" | python3 -c "import sys, json; data=json.load(sys.stdin); print([m['name'] for m in data.get('models', [])])" 2>/dev/null || echo "[]")

    if echo "$models" | grep -q "$OLLAMA_MODEL"; then
        success "Ollama model $OLLAMA_MODEL is available"
    else
        error "Ollama model $OLLAMA_MODEL not found. Available models: $models"
        return 1
    fi

    # Check container status
    log "Checking container status..."
    local unhealthy_containers
    unhealthy_containers=$(docker-compose ps --format "table {{.Name}}\t{{.Status}}" | grep -v "Up" | grep -v "NAME" | wc -l)

    if [ "$unhealthy_containers" -eq 0 ]; then
        success "All containers are healthy"
    else
        error "Some containers are not healthy:"
        docker-compose ps
        return 1
    fi

    success "All health checks passed"
    return 0
}

# ============================================================
# MAIN DEPLOYMENT WORKFLOW
# ============================================================

main() {
    log "Starting deployment script"
    log "Deployment type: $DEPLOY_TYPE"
    log "Environment: $ENVIRONMENT"
    log "Project directory: $PROJECT_DIR"

    # Validate deployment type
    case $DEPLOY_TYPE in
        docker)
            ;;
        *)
            error "Only 'docker' deployment type is supported in this enhanced script"
            exit 1
            ;;
    esac

    # Pre-deployment conflict checks
    info "Performing pre-deployment conflict checks..."

    if ! check_port_conflicts; then
        exit 1
    fi

    if ! check_container_conflicts; then
        exit 1
    fi

    if ! check_network_conflicts; then
        exit 1
    fi

    if ! check_docker_resources; then
        exit 1
    fi

    success "All conflict checks passed"

    # Create backup
    local backup_dir
    backup_dir=$(backup_existing_deployment)

    # Trap for rollback on error
    trap "rollback_deployment '$backup_dir'" ERR

    # Deploy containers
    if ! deploy_containers; then
        error "Container deployment failed"
        exit 1
    fi

    # Setup Ollama model
    if ! setup_ollama_model; then
        error "Ollama model setup failed"
        exit 1
    fi

    # Wait for services
    if ! wait_for_services; then
        error "Services failed to start"
        exit 1
    fi

    # Run health checks
    if ! run_health_checks; then
        error "Health checks failed"
        exit 1
    fi

    # Clear trap
    trap - ERR

    # Show deployment status
    log "Deployment completed successfully"
    echo
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}🎉 Deployment Successful!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo
    info "Deployment Summary:"
    echo "  📁 Project: $PROJECT_DIR"
    echo "  🐳 Containers: ${CONTAINER_NAMES[*]}"
    echo "  🔌 Ports: ${REQUIRED_PORTS[*]}"
    echo "  🌐 Network: $NETWORK_NAME"
    echo "  🤖 Model: $OLLAMA_MODEL"
    echo "  📊 Logs: $LOG_FILE"
    echo
    info "Next Steps:"
    echo "  1. Test bot: curl http://localhost:8000/health"
    echo "  2. Check logs: docker-compose logs -f"
    echo "  3. Test in Nextcloud Talk: @MinecraftBot How do I craft a pickaxe?"
    echo
    info "Management Commands:"
    echo "  📊 Status: docker-compose ps"
    echo "  🔄 Restart: docker-compose restart"
    echo "  🛑 Stop: docker-compose down"
    echo "  📋 Logs: docker-compose logs -f minecraft_bot"
    echo
    success "Bot is ready to answer Minecraft questions!"
}

# Show usage if requested
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "Minecraft Bot Deployment Script"
    echo
    echo "Usage: $0 [deployment-type] [environment]"
    echo
    echo "Arguments:"
    echo "  deployment-type    Type of deployment (default: docker)"
    echo "  environment        Environment (default: production)"
    echo
    echo "Features:"
    echo "  ✅ Port conflict detection"
    echo "  ✅ Container name conflict detection"
    echo "  ✅ Network conflict detection"
    echo "  ✅ Automatic Ollama model setup"
    echo "  ✅ Comprehensive health checks"
    echo "  ✅ Backup and rollback capabilities"
    echo "  ✅ Detailed logging"
    echo
    echo "Examples:"
    echo "  $0 docker production    # Full production deployment"
    echo "  $0 docker development   # Development deployment"
    echo
    exit 0
fi

# Run main function
main "$@"
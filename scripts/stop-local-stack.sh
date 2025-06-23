#!/bin/bash

# Stop Local Stack - Clean shutdown of all Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_info "Stopping Causal Analysis Agent Local Stack"
echo "=============================================="

# Stop individual containers
log_info "Stopping WebSocket Gateway..."
docker stop websocket-gateway 2>/dev/null || true
docker rm websocket-gateway 2>/dev/null || true

log_info "Stopping LocalStack..."
docker stop localstack-simple 2>/dev/null || true
docker rm localstack-simple 2>/dev/null || true

# Stop docker compose services
log_info "Stopping Docker Compose services..."
docker compose down 2>/dev/null || true
docker compose -f docker-compose.local-cloud.yml down 2>/dev/null || true

# Clean up any orphaned containers
log_info "Cleaning up orphaned containers..."
docker container prune -f >/dev/null 2>&1 || true

log_success "🛑 All services stopped"

# Show remaining containers (if any)
remaining=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(causal|localstack|websocket)" || true)
if [[ -n "$remaining" ]]; then
    log_warning "Some containers are still running:"
    echo "$remaining"
else
    log_success "All related containers have been stopped"
fi
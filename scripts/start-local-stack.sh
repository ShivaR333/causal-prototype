#!/bin/bash

# Start Local Stack - Automate building and running all Docker containers
# This script sets up the complete local development environment

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

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [[ ! -f "docker-compose.yml" ]]; then
    log_error "Please run this script from the project root directory"
    exit 1
fi

log_info "Starting Causal Analysis Agent Local Stack"
echo "=============================================="

NETWORK_NAME="causal-local"

# Clean up any existing containers
log_info "Cleaning up existing containers..."
docker rm -f localstack websocket-gateway 2>/dev/null || true
docker compose -f docker-compose.local-cloud.yml down 2>/dev/null || true
docker compose down 2>/dev/null || true
docker network rm $NETWORK_NAME 2>/dev/null || true

# Create network
log_info "Creating Docker network: $NETWORK_NAME"
docker network create $NETWORK_NAME
log_success "Network created"

# Build WebSocket Gateway image
log_info "Building WebSocket Gateway..."
cd local-cloud/websocket-gateway
if [[ ! -f "package-lock.json" ]]; then
    log_info "Installing npm dependencies..."
    npm install
fi
cd ../..

log_info "Building WebSocket Gateway Docker image..."
docker build -t websocket-gateway ./local-cloud/websocket-gateway/
log_success "WebSocket Gateway built"

# Start LocalStack (simple mode)
log_info "Starting LocalStack..."
docker run -d \
    --name localstack \
    --network $NETWORK_NAME \
    -p 4566:4566 \
    -e SERVICES=s3,dynamodb,secretsmanager,cognito-idp,apigateway,lambda,sts,iam,logs,stepfunctions \
    -e DEBUG=1 \
    localstack/localstack:latest

# Wait for LocalStack to be ready
log_info "Waiting for LocalStack to be ready..."
max_attempts=30
attempt=1
while ! curl -sf http://localhost:4566/_localstack/health >/dev/null 2>&1; do
    if [[ $attempt -ge $max_attempts ]]; then
        log_error "LocalStack failed to start after $max_attempts attempts"
        exit 1
    fi
    echo -n "."
    sleep 2
    ((attempt++))
done
echo
log_success "LocalStack is ready"

# Add a delay to ensure all services are ready
log_info "Waiting for 10 seconds for LocalStack services to initialize..."
sleep 10

# Start WebSocket Gateway
log_info "Starting WebSocket Gateway..."
docker run -d \
    --name websocket-gateway \
    --network $NETWORK_NAME \
    -p 8080:8080 \
    -e AWS_ENDPOINT=http://localstack:4566 \
    -e LAMBDA_ENDPOINT=http://host.docker.internal:4566 \
    websocket-gateway

# Wait for WebSocket Gateway to be ready
log_info "Waiting for WebSocket Gateway to be ready..."
max_attempts=15
attempt=1
while ! curl -sf http://localhost:8080/health >/dev/null 2>&1; do
    if [[ $attempt -ge $max_attempts ]]; then
        log_error "WebSocket Gateway failed to start after $max_attempts attempts"
        exit 1
    fi
    echo -n "."
    sleep 2
    ((attempt++))
done
echo
log_success "WebSocket Gateway is ready"

# Start main causal analysis service
log_info "Starting Causal Analysis service..."
docker compose up -d causal-analysis
log_success "Causal Analysis service started"

# Wait for causal analysis to be ready
log_info "Waiting for Causal Analysis API to be ready..."
max_attempts=15
attempt=1
while ! curl -sf http://localhost:8000/ >/dev/null 2>&1; do
    if [[ $attempt -ge $max_attempts ]]; then
        log_error "Causal Analysis API failed to start after $max_attempts attempts"
        exit 1
    fi
    echo -n "."
    sleep 2
    ((attempt++))
done
echo
log_success "Causal Analysis API is ready"

# Optional: Start frontend if available
if [[ -f "frontend/package.json" ]]; then
    log_info "Starting Frontend (if you want to run it)..."
    log_warning "To start frontend manually: cd frontend && npm run dev"
fi

# Show status
echo
log_success "🚀 Local Stack is ready!"
echo "=============================================="
echo "✅ LocalStack:          http://localhost:4566"
echo "✅ WebSocket Gateway:   http://localhost:8080"
echo "✅ Causal Analysis API: http://localhost:8000"
echo "✅ Frontend:            http://localhost:3000 (manual start)"
echo
echo "📊 Health Check:"
./scripts/quick-health-check.sh

echo
log_info "To stop all services, run: ./scripts/stop-local-stack.sh"
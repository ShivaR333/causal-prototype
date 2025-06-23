#!/bin/bash

# Quick Health Check Script
# Fast validation of critical system components

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Quick test function
quick_test() {
    local name="$1"
    local command="$2"
    
    printf "%-40s " "$name"
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        return 1
    fi
}

echo "🚀 Quick Health Check - Causal Analysis Agent"
echo "=============================================="

# Critical service checks
quick_test "Docker is running" "docker info"
quick_test "Docker Compose available" "command -v docker-compose"
quick_test "LocalStack responding" "curl -sf http://localhost:4566/_localstack/health"
quick_test "Frontend accessible" "curl -sf http://localhost:3000"
quick_test "WebSocket Gateway health" "curl -sf http://localhost:8080/health"
quick_test "DynamoDB Admin accessible" "curl -sf http://localhost:8001"

# AWS Resources
quick_test "S3 buckets exist" "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal s3 ls | grep -q causal-analysis-dev"
quick_test "DynamoDB tables exist" "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal dynamodb list-tables | grep -q sessions"
quick_test "Lambda functions deployed" "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal lambda list-functions | grep -q causal-analysis-dev"

# Advanced tests (if Node.js available)
if command -v node > /dev/null 2>&1; then
    quick_test "WebSocket connection works" "node -e \"
        const WebSocket = require('ws');
        const ws = new WebSocket('ws://localhost:8080');
        ws.on('open', () => { ws.close(); process.exit(0); });
        ws.on('error', () => process.exit(1));
        setTimeout(() => process.exit(1), 3000);
    \""
else
    printf "%-40s " "WebSocket connection works"
    echo -e "${YELLOW}⏸️ SKIP (Node.js not available)${NC}"
fi

echo
echo "🎯 Quick health check completed!"
echo "For comprehensive testing, run: ./scripts/automated-test-suite.sh"
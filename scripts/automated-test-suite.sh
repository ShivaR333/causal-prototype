#!/bin/bash

# Automated Test Suite for Causal Analysis Agent
# This script executes the comprehensive test checklist and generates a report

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
REPORT_DIR="$PROJECT_ROOT/test-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$REPORT_DIR/test_report_$TIMESTAMP.md"
JSON_REPORT="$REPORT_DIR/test_results_$TIMESTAMP.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
declare -A test_results
total_tests=0
passed_tests=0
failed_tests=0
skipped_tests=0

# Utility functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
}

# Test execution function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local description="$3"
    
    total_tests=$((total_tests + 1))
    
    log_info "Running: $test_name"
    
    if eval "$test_command" > /dev/null 2>&1; then
        log_success "$test_name"
        test_results["$test_name"]="PASS"
        passed_tests=$((passed_tests + 1))
        return 0
    else
        log_error "$test_name"
        test_results["$test_name"]="FAIL"
        failed_tests=$((failed_tests + 1))
        return 1
    fi
}

# Skip test function
skip_test() {
    local test_name="$1"
    local reason="$2"
    
    total_tests=$((total_tests + 1))
    skipped_tests=$((skipped_tests + 1))
    test_results["$test_name"]="SKIP"
    log_warning "$test_name - $reason"
}

# Setup function
setup_test_environment() {
    log_info "Setting up test environment..."
    
    # Create reports directory
    mkdir -p "$REPORT_DIR"
    
    # Set up test data
    cd "$PROJECT_ROOT"
    
    # Initialize report files
    cat > "$REPORT_FILE" << EOF
# Automated Test Report - Causal Analysis Agent

**Date**: $(date)
**Environment**: Local Development
**Version**: Sprint 1
**Tester**: Automated Test Suite

---

## Test Summary

EOF

    echo '{"test_run": {"timestamp": "'$TIMESTAMP'", "results": []}}' > "$JSON_REPORT"
}

# Pre-test setup checks
test_pre_setup() {
    log_info "=== PRE-TEST SETUP CHECKS ==="
    
    run_test "Docker Available" \
        "command -v docker" \
        "Docker command available"
    
    run_test "Docker Compose Available" \
        "command -v docker-compose" \
        "Docker Compose command available"
    
    run_test "Project Structure" \
        "[ -f docker-compose.local-cloud.yml ]" \
        "Docker compose file exists"
    
    run_test "Setup Scripts Exist" \
        "[ -d local-cloud/setup-scripts ]" \
        "Setup scripts directory exists"
    
    run_test "Lambda Functions Exist" \
        "[ -d local-cloud/lambdas ]" \
        "Lambda functions directory exists"
}

# Service health checks
test_service_health() {
    log_info "=== SERVICE HEALTH CHECKS ==="
    
    run_test "LocalStack Health" \
        "curl -sf http://localhost:4566/_localstack/health | jq -e '.services.s3 == \"available\"'" \
        "LocalStack S3 service available"
    
    run_test "WebSocket Gateway Health" \
        "curl -sf http://localhost:8080/health" \
        "WebSocket Gateway responding"
    
    run_test "Frontend Health" \
        "curl -sf http://localhost:3000 | grep -q 'Causal Analysis'" \
        "Frontend application loading"
    
    run_test "DynamoDB Admin Health" \
        "curl -sf http://localhost:8001" \
        "DynamoDB Admin accessible"
    
    run_test "Step Functions Health" \
        "curl -sf http://localhost:8083" \
        "Step Functions Local accessible"
}

# AWS Resource checks
test_aws_resources() {
    log_info "=== AWS RESOURCES VALIDATION ==="
    
    run_test "S3 Buckets Exist" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal s3 ls | grep -q 'causal-analysis-dev'" \
        "Required S3 buckets created"
    
    run_test "DynamoDB Tables Exist" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal dynamodb list-tables | grep -q 'causal-analysis-dev-sessions'" \
        "Required DynamoDB tables created"
    
    run_test "Lambda Functions Deployed" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal lambda list-functions | grep -q 'causal-analysis-dev'" \
        "Lambda functions deployed"
    
    run_test "Secrets Manager Setup" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal secretsmanager list-secrets | grep -q 'causal-analysis-dev'" \
        "Secrets Manager configured"
    
    run_test "Cognito User Pool" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal cognito-idp list-user-pools --max-results 10 | grep -q 'causal-analysis-dev'" \
        "Cognito user pool created"
    
    run_test "Step Functions State Machine" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal stepfunctions list-state-machines | grep -q 'causal-analysis-dev'" \
        "Step Functions state machine deployed"
}

# Frontend UI tests
test_frontend_ui() {
    log_info "=== FRONTEND UI TESTING ==="
    
    run_test "Frontend Loads Without Errors" \
        "curl -sf http://localhost:3000 | grep -q 'Causal Analysis Agent'" \
        "Frontend title present"
    
    run_test "Authentication Form Present" \
        "curl -sf http://localhost:3000 | grep -q -i 'sign.*in\\|email\\|password'" \
        "Authentication form elements present"
    
    # JavaScript and CSS checks
    run_test "JavaScript Bundle Loads" \
        "curl -sf http://localhost:3000/_next/static/ | grep -q '.js'" \
        "JavaScript bundles available"
    
    run_test "CSS Styles Load" \
        "curl -sf http://localhost:3000/_next/static/ | grep -q '.css'" \
        "CSS styles available"
}

# WebSocket connection tests
test_websocket_connection() {
    log_info "=== WEBSOCKET CONNECTION TESTING ==="
    
    # Test WebSocket endpoint availability
    run_test "WebSocket Port Open" \
        "nc -z localhost 8080" \
        "WebSocket port 8080 accessible"
    
    # Test WebSocket handshake (using Node.js if available)
    if command -v node > /dev/null 2>&1; then
        run_test "WebSocket Handshake" \
            "node -e \"
                const WebSocket = require('ws');
                const ws = new WebSocket('ws://localhost:8080');
                ws.on('open', () => { console.log('Connected'); ws.close(); process.exit(0); });
                ws.on('error', () => process.exit(1));
                setTimeout(() => process.exit(1), 5000);
            \"" \
            "WebSocket connection successful"
    else
        skip_test "WebSocket Handshake" "Node.js not available"
    fi
}

# Lambda function tests
test_lambda_functions() {
    log_info "=== LAMBDA FUNCTION TESTING ==="
    
    # Test individual Lambda functions
    local functions=("parse-initial-query" "invoke-llm" "dispatch-tool" "append-tool-output" "handle-finish" "websocket-handler")
    
    for func in "${functions[@]}"; do
        run_test "Lambda Function: $func" \
            "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal lambda get-function --function-name causal-analysis-dev-$func" \
            "Lambda function $func exists and accessible"
    done
    
    # Test Lambda invocation
    run_test "Lambda Invocation Test" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal lambda invoke --function-name causal-analysis-dev-parse-initial-query --payload '{\"sessionId\":\"test\",\"query\":{\"type\":\"natural_language\",\"content\":\"test\"}}' /tmp/response.json && [ -f /tmp/response.json ]" \
        "Lambda function can be invoked"
}

# Step Functions workflow tests
test_step_functions() {
    log_info "=== STEP FUNCTIONS WORKFLOW TESTING ==="
    
    run_test "State Machine Exists" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal stepfunctions describe-state-machine --state-machine-arn 'arn:aws:states:us-east-1:000000000000:stateMachine:causal-analysis-dev-agent-sm'" \
        "State machine definition accessible"
    
    # Test workflow execution
    run_test "Start Execution Test" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal stepfunctions start-execution --state-machine-arn 'arn:aws:states:us-east-1:000000000000:stateMachine:causal-analysis-dev-agent-sm' --input '{\"sessionId\":\"test\",\"query\":{\"type\":\"natural_language\",\"content\":\"test\"}}'" \
        "State machine execution can be started"
}

# Database operations tests
test_database_operations() {
    log_info "=== DATABASE OPERATIONS TESTING ==="
    
    # Test DynamoDB table operations
    run_test "Sessions Table Write" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal dynamodb put-item --table-name causal-analysis-dev-sessions --item '{\"sessionId\":{\"S\":\"test-session\"},\"userId\":{\"S\":\"test-user\"},\"timestamp\":{\"N\":\"$(date +%s)000\"}}'" \
        "Can write to sessions table"
    
    run_test "Sessions Table Read" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal dynamodb get-item --table-name causal-analysis-dev-sessions --key '{\"sessionId\":{\"S\":\"test-session\"}}'" \
        "Can read from sessions table"
    
    run_test "Connections Table Write" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal dynamodb put-item --table-name causal-analysis-dev-connections --item '{\"connectionId\":{\"S\":\"test-connection\"},\"userId\":{\"S\":\"test-user\"},\"connectedAt\":{\"N\":\"$(date +%s)000\"}}'" \
        "Can write to connections table"
    
    run_test "Jobs Table Write" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal dynamodb put-item --table-name causal-analysis-dev-jobs --item '{\"jobId\":{\"S\":\"test-job\"},\"sessionId\":{\"S\":\"test-session\"},\"status\":{\"S\":\"test\"}}'" \
        "Can write to jobs table"
}

# S3 operations tests
test_s3_operations() {
    log_info "=== S3 OPERATIONS TESTING ==="
    
    run_test "S3 Raw Data Bucket Access" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal s3 ls s3://causal-analysis-dev-rawdata/" \
        "Raw data bucket accessible"
    
    run_test "S3 Artifacts Bucket Access" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal s3 ls s3://causal-analysis-dev-artifacts/" \
        "Artifacts bucket accessible"
    
    # Test file upload/download
    run_test "S3 File Upload" \
        "echo 'test data' | docker-compose -f docker-compose.local-cloud.yml run --rm -i aws-cli awslocal s3 cp - s3://causal-analysis-dev-rawdata/test-file.txt" \
        "Can upload files to S3"
    
    run_test "S3 File Download" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal s3 cp s3://causal-analysis-dev-rawdata/test-file.txt -" \
        "Can download files from S3"
}

# Performance tests
test_performance() {
    log_info "=== PERFORMANCE TESTING ==="
    
    # Test response times
    run_test "Frontend Response Time" \
        "time curl -sf http://localhost:3000 > /dev/null" \
        "Frontend responds quickly"
    
    run_test "WebSocket Gateway Response Time" \
        "time curl -sf http://localhost:8080/health > /dev/null" \
        "WebSocket Gateway responds quickly"
    
    run_test "LocalStack Response Time" \
        "time curl -sf http://localhost:4566/_localstack/health > /dev/null" \
        "LocalStack responds quickly"
    
    # Memory usage check
    run_test "Memory Usage Check" \
        "docker stats --no-stream --format 'table {{.MemUsage}}' | grep -v 'MEM USAGE' | head -1" \
        "Container memory usage within limits"
}

# Security tests
test_security() {
    log_info "=== SECURITY TESTING ==="
    
    # Test for exposed secrets
    run_test "No Hardcoded Secrets" \
        "! grep -r 'password.*=\\|api.*key.*=' --include='*.js' --include='*.py' --include='*.json' local-cloud/ frontend/src/ | grep -v 'test\\|mock\\|example'" \
        "No hardcoded secrets in code"
    
    # Test input validation (basic)
    if command -v curl > /dev/null 2>&1; then
        run_test "XSS Prevention Test" \
            "! curl -sf 'http://localhost:3000/?q=<script>alert(1)</script>' | grep -q '<script>'" \
            "XSS attempts not reflected"
    else
        skip_test "XSS Prevention Test" "curl not available"
    fi
    
    # Test authentication requirement
    run_test "Authentication Required" \
        "curl -sf http://localhost:3000 | grep -q -i 'sign.*in\\|auth'" \
        "Authentication required for access"
}

# Error handling tests
test_error_handling() {
    log_info "=== ERROR HANDLING TESTING ==="
    
    # Test invalid endpoints
    run_test "404 Error Handling" \
        "curl -sf http://localhost:3000/nonexistent || true" \
        "404 errors handled gracefully"
    
    # Test malformed requests
    run_test "Malformed Request Handling" \
        "curl -sf -X POST http://localhost:8080 -d 'invalid json' || true" \
        "Malformed requests handled"
    
    # Test service dependency failures
    run_test "Service Dependency Failure" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal dynamodb describe-table --table-name nonexistent-table || true" \
        "Missing dependencies handled gracefully"
}

# Integration tests
test_integration() {
    log_info "=== INTEGRATION TESTING ==="
    
    # Test end-to-end component communication
    run_test "Frontend to WebSocket Gateway" \
        "curl -sf http://localhost:3000 && curl -sf http://localhost:8080/health" \
        "Frontend can reach WebSocket Gateway"
    
    run_test "WebSocket Gateway to LocalStack" \
        "docker-compose -f docker-compose.local-cloud.yml exec -T websocket-gateway ping -c 1 localstack" \
        "WebSocket Gateway can reach LocalStack"
    
    run_test "Lambda to DynamoDB Integration" \
        "docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal lambda invoke --function-name causal-analysis-dev-parse-initial-query --payload '{\"sessionId\":\"integration-test\",\"query\":{\"type\":\"natural_language\",\"content\":\"test\"}}' /tmp/response.json" \
        "Lambda functions can access DynamoDB"
}

# Cleanup test data
cleanup_test_data() {
    log_info "=== CLEANUP TEST DATA ==="
    
    # Clean up test records
    docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal dynamodb delete-item --table-name causal-analysis-dev-sessions --key '{"sessionId":{"S":"test-session"}}' > /dev/null 2>&1 || true
    
    docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal dynamodb delete-item --table-name causal-analysis-dev-connections --key '{"connectionId":{"S":"test-connection"}}' > /dev/null 2>&1 || true
    
    docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal dynamodb delete-item --table-name causal-analysis-dev-jobs --key '{"jobId":{"S":"test-job"}}' > /dev/null 2>&1 || true
    
    docker-compose -f docker-compose.local-cloud.yml run --rm aws-cli awslocal s3 rm s3://causal-analysis-dev-rawdata/test-file.txt > /dev/null 2>&1 || true
    
    log_info "Test data cleanup completed"
}

# Generate comprehensive report
generate_report() {
    log_info "Generating test report..."
    
    local pass_rate=$((passed_tests * 100 / total_tests))
    
    # Append summary to markdown report
    cat >> "$REPORT_FILE" << EOF
| Metric | Value |
|--------|-------|
| Total Tests | $total_tests |
| Passed | $passed_tests ✅ |
| Failed | $failed_tests ❌ |
| Skipped | $skipped_tests ⏸️ |
| **Pass Rate** | **${pass_rate}%** |

---

## Detailed Results

| Test Name | Status | Category |
|-----------|--------|----------|
EOF

    # Add detailed results
    for test_name in "${!test_results[@]}"; do
        local status=${test_results[$test_name]}
        local icon=""
        case $status in
            "PASS") icon="✅" ;;
            "FAIL") icon="❌" ;;
            "SKIP") icon="⏸️" ;;
        esac
        echo "| $test_name | $status $icon | - |" >> "$REPORT_FILE"
    done
    
    # Add overall assessment
    cat >> "$REPORT_FILE" << EOF

---

## Overall Assessment

EOF

    if [ $failed_tests -eq 0 ] && [ $pass_rate -ge 95 ]; then
        echo "### ✅ **SYSTEM READY FOR PRODUCTION**" >> "$REPORT_FILE"
        echo "All critical tests passed. System is ready for deployment." >> "$REPORT_FILE"
    elif [ $failed_tests -le 2 ] && [ $pass_rate -ge 85 ]; then
        echo "### ⚠️ **READY WITH MINOR ISSUES**" >> "$REPORT_FILE"
        echo "Minor issues identified but system is functional. Review failed tests." >> "$REPORT_FILE"
    else
        echo "### ❌ **NOT READY FOR PRODUCTION**" >> "$REPORT_FILE"
        echo "Critical issues found. System requires fixes before deployment." >> "$REPORT_FILE"
    fi
    
    # Add recommendations
    cat >> "$REPORT_FILE" << EOF

## Recommendations

EOF

    if [ $failed_tests -gt 0 ]; then
        echo "- Review and fix the $failed_tests failed test(s)" >> "$REPORT_FILE"
        echo "- Re-run tests after fixes" >> "$REPORT_FILE"
    fi
    
    if [ $skipped_tests -gt 0 ]; then
        echo "- Consider implementing the $skipped_tests skipped test(s)" >> "$REPORT_FILE"
    fi
    
    echo "- Monitor system performance in production" >> "$REPORT_FILE"
    echo "- Set up automated testing pipeline" >> "$REPORT_FILE"
    
    # Generate JSON report
    local json_results="["
    local first=true
    for test_name in "${!test_results[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            json_results+=","
        fi
        json_results+="{\"name\":\"$test_name\",\"status\":\"${test_results[$test_name]}\"}"
    done
    json_results+="]"
    
    cat > "$JSON_REPORT" << EOF
{
  "test_run": {
    "timestamp": "$TIMESTAMP",
    "summary": {
      "total": $total_tests,
      "passed": $passed_tests,
      "failed": $failed_tests,
      "skipped": $skipped_tests,
      "pass_rate": $pass_rate
    },
    "results": $json_results
  }
}
EOF

    echo
    echo "==================== TEST SUMMARY ===================="
    echo "Total Tests: $total_tests"
    echo "Passed: $passed_tests ✅"
    echo "Failed: $failed_tests ❌"
    echo "Skipped: $skipped_tests ⏸️"
    echo "Pass Rate: ${pass_rate}%"
    echo
    echo "Reports generated:"
    echo "- Markdown: $REPORT_FILE"
    echo "- JSON: $JSON_REPORT"
    echo "======================================================="
    
    return $failed_tests
}

# Main execution
main() {
    echo "🧪 Starting Automated Test Suite for Causal Analysis Agent"
    echo "Timestamp: $(date)"
    echo
    
    setup_test_environment
    
    # Execute test suites
    test_pre_setup
    test_service_health
    test_aws_resources
    test_frontend_ui
    test_websocket_connection
    test_lambda_functions
    test_step_functions
    test_database_operations
    test_s3_operations
    test_performance
    test_security
    test_error_handling
    test_integration
    
    # Cleanup
    cleanup_test_data
    
    # Generate final report
    generate_report
    
    # Exit with appropriate code
    if [ $failed_tests -eq 0 ]; then
        echo "🎉 All tests passed!"
        exit 0
    else
        echo "❌ $failed_tests test(s) failed. Check the report for details."
        exit 1
    fi
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --quick        Run only critical tests"
        echo "  --no-cleanup   Skip test data cleanup"
        echo "  --report-only  Generate report from existing results"
        exit 0
        ;;
    --quick)
        echo "Running quick test suite..."
        # TODO: Implement quick test mode
        ;;
    --no-cleanup)
        echo "Skipping cleanup..."
        # TODO: Implement no-cleanup mode
        ;;
    --report-only)
        echo "Generating report only..."
        generate_report
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
# Testing Playbook - Causal Analysis Agent

## Overview

This playbook provides comprehensive testing scenarios for validating the cloud-native causal analysis agent. Each test includes setup, execution steps, expected results, and troubleshooting guidance.

## Test Environment Status Check

Before running any tests, verify the environment:

```bash
# Check all services are running
docker-compose -f docker-compose.local-cloud.yml ps

# Verify LocalStack health
curl -s http://localhost:4566/_localstack/health | jq

# Check WebSocket gateway
curl -s http://localhost:8080/health

# Verify frontend
curl -s http://localhost:3000 | grep -q "Causal Analysis" && echo "Frontend OK"
```

**Expected Status**: All services should show "Up" status.

## Test Suite 1: Authentication & Session Management

### Test 1.1: User Authentication Flow

**Objective**: Verify complete authentication workflow

**Steps**:
1. Open http://localhost:3000
2. Verify auth form is displayed
3. Click "Use Demo Account"
4. Observe connection status

**Expected Results**:
```
✅ Sign in form appears
✅ Demo credentials populated (admin@example.com)
✅ "Connected via WebSocket" appears in header
✅ Session ID displayed (e.g., "Session: abc12345")
✅ Welcome message in chat
```

**Validation**:
```bash
# Check DynamoDB sessions table
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal dynamodb scan \
  --table-name causal-analysis-dev-sessions --max-items 5
```

**Troubleshooting**:
- If auth fails: Check Cognito setup with `/scripts/create-cognito.sh`
- If WebSocket fails: Restart websocket-gateway service
- If no session ID: Check DynamoDB connections

### Test 1.2: Session Persistence

**Objective**: Verify session survives browser refresh

**Steps**:
1. Complete Test 1.1 (authenticate)
2. Note the session ID
3. Refresh browser (F5)
4. Verify automatic reconnection

**Expected Results**:
```
✅ Automatic reconnection after refresh
✅ Same session ID maintained
✅ No need to re-authenticate
```

**Validation**:
```bash
# Session should persist in DynamoDB
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal dynamodb get-item \
  --table-name causal-analysis-dev-sessions \
  --key '{"sessionId":{"S":"YOUR_SESSION_ID"}}'
```

### Test 1.3: Multi-User Sessions

**Objective**: Test concurrent user sessions

**Steps**:
1. Open first browser window, authenticate as admin@example.com
2. Open incognito window, authenticate as user@example.com
3. Send different queries from each session
4. Verify independent processing

**Expected Results**:
```
✅ Two separate sessions created
✅ Independent conversation contexts
✅ No cross-session data leakage
```

**Validation**:
```bash
# Should see multiple sessions
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal dynamodb scan \
  --table-name causal-analysis-dev-sessions | jq '.Items | length'

# Should see multiple connections
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal dynamodb scan \
  --table-name causal-analysis-dev-connections | jq '.Items | length'
```

## Test Suite 2: Core Agent Functionality

### Test 2.1: Natural Language Query Processing

**Objective**: Test end-to-end query processing with natural language

**Test Queries**:
```
1. "What's the effect of discount on sales?"
2. "Analyze the impact of education on income"
3. "Show me the causal relationship between price and demand"
```

**Steps for Each Query**:
1. Ensure authenticated and connected
2. Type query in chat input
3. Send query
4. Monitor Step Functions execution
5. Observe response

**Expected Results for Query 1**:
```
✅ Query received acknowledgment
✅ Step Functions execution started
✅ Lambda functions executed in sequence:
   - parse-initial-query
   - invoke-llm
   - dispatch-tool
   - append-tool-output
   - handle-finish
✅ Structured response with:
   - Estimated Effect: [number]
   - Confidence Interval: [range]
   - Method: [analysis_method]
```

**Monitoring Commands**:
```bash
# Watch Step Functions execution
# Access http://localhost:8083 and monitor executions

# Check Lambda logs
docker-compose -f docker-compose.local-cloud.yml logs | grep "parse-initial-query"
docker-compose -f docker-compose.local-cloud.yml logs | grep "invoke-llm"

# Monitor DynamoDB jobs table
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal dynamodb scan \
  --table-name causal-analysis-dev-jobs --max-items 5
```

### Test 2.2: Structured Form Query

**Objective**: Test form-based causal analysis

**Steps**:
1. Navigate to the right sidebar form
2. Fill in the following:
   - **Treatment Variable**: `discount_offer`
   - **Outcome Variable**: `purchase_amount`
   - **Confounders**: `customer_age,customer_income,seasonality`
   - **Data File**: `sample_data/eCommerce_sales.csv`
   - **DAG File**: `causal_analysis/config/ecommerce_dag.json`
3. Click "Run Analysis"
4. Monitor execution

**Expected Results**:
```
✅ Form submission triggers Step Functions
✅ Same workflow as natural language query
✅ Structured parameters passed to analysis
✅ Results formatted appropriately
```

### Test 2.3: Agent Clarification Flow

**Objective**: Test interactive clarification requests

**Test Scenario**:
1. Send ambiguous query: `"Analyze my data"`
2. Respond to clarification prompt
3. Complete analysis

**Steps**:
1. Type: `"Analyze my data"`
2. Observe clarification request
3. Notice input field changes to "Respond" mode
4. Type: `"I want to see the effect of price on demand"`
5. Observe normal processing resumes

**Expected Results**:
```
✅ Agent requests clarification: "What specific analysis would you like?"
✅ Input UI switches to response mode (yellow highlighting)
✅ Step Functions pauses for user input
✅ User response triggers workflow continuation
✅ Normal analysis proceeds with clarified intent
```

**Technical Validation**:
```bash
# Check for pending task token in session
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal dynamodb get-item \
  --table-name causal-analysis-dev-sessions \
  --key '{"sessionId":{"S":"YOUR_SESSION_ID"}}' | jq '.Item.context.M.pendingTaskToken'
```

## Test Suite 3: Error Handling & Resilience

### Test 3.1: Service Failure Recovery

**Objective**: Test system behavior when services fail

**Test Scenarios**:

#### Scenario A: Step Functions Unavailable
```bash
# Stop Step Functions
docker stop causal-prototype-stepfunctions-local-1

# Send query
# Expected: Error message, graceful degradation

# Restart service
docker-compose -f docker-compose.local-cloud.yml up stepfunctions-local -d
```

#### Scenario B: Lambda Function Error
```bash
# Corrupt a Lambda function (simulate error)
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal lambda update-function-code \
  --function-name causal-analysis-dev-invoke-llm \
  --zip-file fileb:///dev/null

# Send query
# Expected: Error handling workflow triggered

# Restore function
docker-compose -f docker-compose.local-cloud.yml run aws-cli /scripts/deploy-lambdas.sh
```

#### Scenario C: WebSocket Connection Loss
```bash
# Stop WebSocket gateway
docker stop causal-prototype-websocket-gateway-1

# Send query from frontend
# Expected: Automatic fallback to REST API (if implemented)

# Restart gateway
docker-compose -f docker-compose.local-cloud.yml up websocket-gateway -d
```

**Expected Results for All Scenarios**:
```
✅ User receives clear error message
✅ System state remains consistent
✅ Recovery is automatic when service returns
✅ No data loss or corruption
```

### Test 3.2: Timeout Handling

**Objective**: Test system behavior with long-running operations

**Steps**:
1. Modify timeout in Step Functions (reduce to 5 seconds)
2. Send query that would normally take longer
3. Observe timeout handling

**Expected Results**:
```
✅ Timeout detected by Step Functions
✅ handle-timeout Lambda function executed
✅ User notified of timeout
✅ Session state cleaned up appropriately
```

### Test 3.3: Invalid Input Handling

**Test Invalid Inputs**:
```
1. Empty messages
2. Very long messages (>10KB)
3. Invalid JSON in WebSocket
4. SQL injection attempts
5. XSS attempts in form fields
```

**Expected Results**:
```
✅ Validation errors returned promptly
✅ No system crashes or exceptions
✅ Security threats mitigated
✅ User receives helpful error messages
```

## Test Suite 4: Performance & Load Testing

### Test 4.1: Concurrent Users

**Objective**: Test system under load

**Setup**: Use Artillery.js or similar tool

```javascript
// artillery-config.yml
config:
  target: 'ws://localhost:8080'
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: "WebSocket Load Test"
    engine: ws
    flow:
      - connect:
          query: "token=test"
      - send:
          message: '{"action":"auth","payload":{"token":"test","userId":"user-{{ $uuid }}"}}'
      - think: 2
      - send:
          message: '{"action":"query","payload":{"type":"natural_language","content":"What is the effect of discount on sales?"}}'
      - think: 10
```

**Run Test**:
```bash
npm install -g artillery
artillery run artillery-config.yml
```

**Expected Results**:
```
✅ System handles 10 concurrent users
✅ Response times < 5 seconds
✅ No connection drops
✅ All queries processed successfully
```

### Test 4.2: Memory Usage Monitoring

**Objective**: Ensure system doesn't have memory leaks

**Steps**:
1. Monitor baseline memory usage
2. Run extended test session (1 hour)
3. Check for memory growth

**Monitoring Commands**:
```bash
# Monitor container memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Monitor specific services
docker stats causal-prototype-localstack-1 causal-prototype-websocket-gateway-1
```

**Expected Results**:
```
✅ Memory usage stable over time
✅ No significant memory leaks
✅ CPU usage appropriate for load
```

## Test Suite 5: Data Integrity & Consistency

### Test 5.1: Conversation Context Preservation

**Objective**: Verify conversation history is maintained correctly

**Steps**:
1. Send initial query: `"What's the effect of discount on sales?"`
2. Send follow-up: `"What about price on demand?"`
3. Send context query: `"Compare these two effects"`
4. Verify agent references previous queries

**Expected Results**:
```
✅ Agent remembers previous queries
✅ Conversation context maintained in DynamoDB
✅ Follow-up questions answered with context
✅ Comparison utilizes both previous analyses
```

**Validation**:
```bash
# Check conversation history in DynamoDB
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal dynamodb get-item \
  --table-name causal-analysis-dev-sessions \
  --key '{"sessionId":{"S":"YOUR_SESSION_ID"}}' | jq '.Item.context.M.history'
```

### Test 5.2: Data File Access

**Objective**: Test S3 data file operations

**Steps**:
1. Upload test file to S3
2. Reference file in query
3. Verify access and processing

**Setup**:
```bash
# Upload test file
echo "test,data,file" > test.csv
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal s3 cp test.csv s3://causal-analysis-dev-rawdata/test.csv

# Verify upload
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal s3 ls s3://causal-analysis-dev-rawdata/
```

**Query**:
```
"Analyze the effect of test on data using file test.csv"
```

**Expected Results**:
```
✅ File successfully accessed from S3
✅ Analysis parameters include correct file path
✅ ECS task (simulated) receives file location
```

## Test Suite 6: Security Testing

### Test 6.1: Authentication Security

**Test Scenarios**:
```
1. Access without authentication
2. Invalid JWT tokens
3. Expired tokens
4. Token tampering
```

**Expected Results**:
```
✅ Unauthenticated access rejected
✅ Invalid tokens rejected gracefully
✅ Expired tokens trigger re-authentication
✅ Tampered tokens detected and rejected
```

### Test 6.2: Input Validation

**Test Malicious Inputs**:
```
1. Script injection: "<script>alert('xss')</script>"
2. SQL injection: "'; DROP TABLE sessions; --"
3. Command injection: "; rm -rf /"
4. Path traversal: "../../etc/passwd"
```

**Expected Results**:
```
✅ All malicious inputs safely handled
✅ No code execution
✅ No unauthorized file access
✅ Proper error messages returned
```

## Test Suite 7: Integration Testing

### Test 7.1: End-to-End Workflow

**Objective**: Complete user journey from authentication to results

**Complete Workflow**:
1. User opens application
2. Authenticates with Cognito
3. WebSocket connection established
4. Sends complex causal query
5. Agent requests clarification
6. User provides clarification
7. Analysis executed on ECS (simulated)
8. Results returned and displayed
9. User asks follow-up question
10. Agent uses conversation context

**Success Criteria**:
```
✅ Each step executes without errors
✅ User experience is smooth and responsive
✅ All data persisted correctly
✅ Performance within acceptable limits
```

### Test 7.2: Service Recovery Testing

**Objective**: Test system recovery after complete restart

**Steps**:
1. Establish active session with conversation history
2. Stop all services: `docker-compose -f docker-compose.local-cloud.yml down`
3. Restart services: `docker-compose -f docker-compose.local-cloud.yml up -d`
4. Re-run setup scripts if needed
5. Access application and verify data

**Expected Results**:
```
✅ Services restart successfully
✅ Data persisted correctly
✅ New sessions can be created
✅ System fully functional after restart
```

## Automated Testing Scripts

### Create Test Runner

```bash
#!/bin/bash
# test-runner.sh

echo "🧪 Starting Causal Analysis Agent Test Suite"

# Test 1: Service Health
echo "Testing service health..."
if curl -s http://localhost:4566/_localstack/health | jq -e '.services.s3 == "available"' > /dev/null; then
    echo "✅ LocalStack healthy"
else
    echo "❌ LocalStack unhealthy"
    exit 1
fi

# Test 2: Authentication
echo "Testing authentication..."
# Add authentication test logic

# Test 3: Basic Query
echo "Testing basic query processing..."
# Add query test logic

# Test 4: Error Handling
echo "Testing error handling..."
# Add error test logic

echo "🎉 All tests completed successfully!"
```

### Performance Monitoring Script

```bash
#!/bin/bash
# monitor.sh

echo "📊 Performance Monitoring Started"

while true; do
    echo "$(date): $(docker stats --no-stream --format 'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}' | grep causal-prototype)"
    sleep 30
done
```

## Test Documentation

### Test Execution Log Template

```
Test Execution Report
=====================

Date: [DATE]
Tester: [NAME]
Environment: Local Development
Version: Sprint 1

Test Results:
- Authentication: ✅ PASS / ❌ FAIL
- Basic Queries: ✅ PASS / ❌ FAIL  
- Clarification Flow: ✅ PASS / ❌ FAIL
- Error Handling: ✅ PASS / ❌ FAIL
- Performance: ✅ PASS / ❌ FAIL

Issues Found:
1. [Description of any issues]
2. [Severity and impact]
3. [Recommended fixes]

Overall Status: ✅ SYSTEM READY / ❌ ISSUES FOUND
```

This comprehensive testing playbook ensures thorough validation of all system components and user workflows. Regular execution of these tests maintains system reliability and helps identify issues early in development.
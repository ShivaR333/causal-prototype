# Test Checklist - Causal Analysis Agent

## Overview
This checklist provides a comprehensive list of all tests that need to be executed to validate the Causal Analysis Agent system. Use this for systematic testing, release validation, and ensuring complete coverage.

---

## 🚀 Pre-Test Setup

### Environment Preparation
- [ ] Docker Desktop running with 8GB+ RAM allocated
- [ ] All ports available (3000, 4566, 8001, 8080, 8083)
- [ ] Git repository cloned and up-to-date
- [ ] Environment variables configured (if any)

### Service Startup
- [ ] `docker-compose -f docker-compose.local-cloud.yml up -d` executed successfully
- [ ] All services show "Up" status in `docker-compose ps`
- [ ] LocalStack health check passes: `curl http://localhost:4566/_localstack/health`
- [ ] Setup scripts executed: `/scripts/create-resources.sh`
- [ ] Lambda functions deployed: `/scripts/deploy-lambdas.sh`

### Service Health Verification
- [ ] Frontend accessible at http://localhost:3000
- [ ] WebSocket Gateway health check at http://localhost:8080/health
- [ ] DynamoDB Admin accessible at http://localhost:8001
- [ ] Step Functions Local accessible at http://localhost:8083
- [ ] LocalStack dashboard accessible at http://localhost:4566

---

## 📱 Frontend & UI Testing

### Initial Load
- [ ] Frontend loads without errors
- [ ] Authentication form displays correctly
- [ ] No console errors in browser developer tools
- [ ] Responsive design works on different screen sizes
- [ ] All UI components render properly

### Authentication UI
- [ ] Sign-in form displays email and password fields
- [ ] "Use Demo Account" button populates credentials correctly
- [ ] Form validation works (empty fields, invalid email format)
- [ ] Error messages display appropriately
- [ ] Loading states show during authentication
- [ ] Success redirects to main chat interface

### Chat Interface
- [ ] Chat messages display correctly (user, assistant, system)
- [ ] Message timestamps are accurate
- [ ] Message input field accepts text
- [ ] Send button enables/disables appropriately
- [ ] Loading indicators appear during processing
- [ ] Error messages display in chat
- [ ] Markdown formatting renders correctly in responses

### Sidebar Form
- [ ] Causal Analysis form displays all fields
- [ ] Dropdown selections work properly
- [ ] Form validation prevents invalid submissions
- [ ] Submit button triggers analysis
- [ ] Form disables during processing
- [ ] Results integrate with chat interface

### Navigation & Controls
- [ ] Sign out button works correctly
- [ ] Session ID displays in header
- [ ] Connection status indicator updates accurately
- [ ] Browser refresh preserves authentication state
- [ ] Back/forward browser navigation handled gracefully

---

## 🔐 Authentication & Session Management

### User Authentication
- [ ] Demo account login (`admin@example.com` / `AdminPass123!`)
- [ ] Test user login (`user@example.com` / `UserPass123!`)
- [ ] Invalid credentials rejected
- [ ] Empty credentials rejected
- [ ] Malformed email addresses rejected
- [ ] Password requirements enforced (if any)

### Session Creation & Management
- [ ] Session created in DynamoDB after authentication
- [ ] Unique session ID generated for each login
- [ ] Session persists across browser refresh
- [ ] Session expires appropriately (if timeout configured)
- [ ] Multiple concurrent sessions supported
- [ ] Session data isolated between users

### Token Management
- [ ] JWT tokens generated correctly
- [ ] Token validation works for WebSocket authentication
- [ ] Invalid tokens rejected
- [ ] Expired tokens handled gracefully
- [ ] Token refresh works (if implemented)
- [ ] Logout clears tokens and session data

### WebSocket Connection
- [ ] WebSocket connection establishes after authentication
- [ ] Connection authenticated successfully with JWT
- [ ] Connection status updates in UI
- [ ] Connection persists during normal operation
- [ ] Reconnection works after temporary disconnection
- [ ] Connection cleanup on logout

---

## 🤖 Core Agent Functionality

### Natural Language Query Processing
- [ ] Basic causal queries: "What's the effect of discount on sales?"
- [ ] Impact analysis: "Analyze the impact of education on income"
- [ ] Relationship queries: "Show causal relationship between price and demand"
- [ ] Complex queries with multiple variables
- [ ] Queries with confounders specified
- [ ] Edge case queries (very short, very long, special characters)

### Query Understanding & Parsing
- [ ] parse-initial-query Lambda function executes
- [ ] User queries parsed correctly into structured format
- [ ] Context from previous queries incorporated
- [ ] Session state updated with query information
- [ ] Error handling for malformed queries
- [ ] Timeout handling for parsing

### LLM Integration
- [ ] invoke-llm Lambda function executes
- [ ] Mock LLM responses generated correctly
- [ ] Real LLM integration (if API key provided)
- [ ] Response format validation (JSON structure)
- [ ] Different response types handled (tool_call, need_input, final_answer)
- [ ] Error handling for LLM failures
- [ ] Timeout handling for LLM calls

### Tool Dispatch & Routing
- [ ] dispatch-tool Lambda function executes
- [ ] Causal analysis tool selection
- [ ] EDA analysis tool selection
- [ ] Data query tool selection
- [ ] Tool parameters configured correctly
- [ ] Job records created in DynamoDB
- [ ] S3 paths configured for tool execution

### Response Processing
- [ ] append-tool-output Lambda function executes
- [ ] Tool results integrated into conversation context
- [ ] Conversation history maintained
- [ ] Context size management (truncation if needed)
- [ ] Session state updated correctly
- [ ] Error handling for malformed tool outputs

### Final Response Handling
- [ ] handle-finish Lambda function executes
- [ ] Responses formatted correctly for frontend
- [ ] Metadata included (timestamps, tool usage)
- [ ] Session completion status updated
- [ ] Final response delivered via WebSocket
- [ ] Response display in frontend chat

---

## 🔄 Step Functions Workflow

### Workflow Execution
- [ ] State machine starts correctly from WebSocket trigger
- [ ] All workflow states execute in proper sequence
- [ ] ParseInitialQuery → InvokeLLM → CheckResponse flow
- [ ] Tool dispatch routing works correctly
- [ ] Error handling states execute when needed
- [ ] Workflow completes successfully

### State Transitions
- [ ] CheckResponse routes to correct next state
- [ ] Tool selection branches work (EDA vs Causal Analysis)
- [ ] User prompt flow (SendPrompt → wait → continue)
- [ ] Error states handle failures appropriately
- [ ] Timeout states manage long operations
- [ ] Final states complete workflow properly

### Execution Monitoring
- [ ] Executions visible in Step Functions Local (http://localhost:8083)
- [ ] Execution history preserved
- [ ] State transition logs available
- [ ] Error details captured in failed executions
- [ ] Input/output data preserved for debugging
- [ ] Performance metrics available

### Parallel Execution
- [ ] Multiple workflows can execute concurrently
- [ ] No resource conflicts between parallel executions
- [ ] Session isolation maintained across workflows
- [ ] Performance acceptable under concurrent load
- [ ] Error in one execution doesn't affect others

---

## 💾 Data Persistence & Storage

### DynamoDB Operations

#### Sessions Table
- [ ] Session records created on authentication
- [ ] Session data updated during conversation
- [ ] Context history preserved correctly
- [ ] Session retrieval by sessionId works
- [ ] Session cleanup on logout
- [ ] TTL handling (if configured)

#### Connections Table
- [ ] Connection records created for WebSocket connections
- [ ] Connection tracking by userId
- [ ] Connection cleanup on disconnect
- [ ] TTL expiration works correctly
- [ ] Multiple connections per user supported

#### Jobs Table
- [ ] Job records created for tool executions
- [ ] Job status updates (dispatched → running → completed)
- [ ] Job parameters preserved correctly
- [ ] Job history queryable by session
- [ ] Job cleanup via TTL
- [ ] Error status handling

### S3 Operations
- [ ] Raw data bucket accessible
- [ ] Sample data files present and readable
- [ ] Artifacts bucket writable
- [ ] File paths generated correctly for tools
- [ ] Bucket permissions configured properly
- [ ] Lifecycle policies working (if configured)

### Secrets Management
- [ ] API keys retrievable from Secrets Manager
- [ ] JWT secrets accessible
- [ ] Secret rotation supported (if implemented)
- [ ] Access permissions configured correctly
- [ ] Error handling for missing secrets

---

## 🎯 Interactive Features

### Clarification Flow
- [ ] Ambiguous queries trigger clarification requests
- [ ] SendPrompt Lambda executes correctly
- [ ] Step Functions pauses for user input
- [ ] WebSocket delivers prompt to frontend
- [ ] Frontend switches to response mode
- [ ] User response triggers workflow continuation
- [ ] Clarified query processed normally

### Test Scenarios
- [ ] Query: "Analyze my data" → clarification → specific analysis
- [ ] Query: "Run analysis" → clarification → structured query
- [ ] Query: "Help me understand" → clarification → focused response
- [ ] Multiple clarification rounds if needed
- [ ] Clarification timeout handling
- [ ] User cancellation of clarification

### Context Awareness
- [ ] Follow-up questions reference previous queries
- [ ] Agent remembers analysis results
- [ ] Conversation context influences responses
- [ ] Context preserved across clarifications
- [ ] Context size management
- [ ] Context reset functionality

---

## ⚡ Performance Testing

### Response Times
- [ ] Authentication completes within 2 seconds
- [ ] WebSocket connection establishes within 1 second
- [ ] Simple queries processed within 5 seconds
- [ ] Complex queries processed within 10 seconds
- [ ] Clarification prompts delivered within 2 seconds
- [ ] Final responses delivered within acceptable time

### Throughput Testing
- [ ] System handles 5 concurrent users
- [ ] System handles 10 concurrent users
- [ ] System handles 20 concurrent users
- [ ] Query processing doesn't degrade with load
- [ ] WebSocket connections stable under load
- [ ] Database operations performant under load

### Resource Usage
- [ ] Memory usage remains stable over time
- [ ] CPU usage appropriate for workload
- [ ] No memory leaks detected
- [ ] Container resource limits respected
- [ ] Network bandwidth usage reasonable
- [ ] Disk space usage controlled

### Stress Testing
- [ ] Extended operation (1+ hours) without degradation
- [ ] Recovery after resource exhaustion
- [ ] Graceful handling of resource limits
- [ ] Performance monitoring during stress
- [ ] System stability under extreme load

---

## 🛡️ Error Handling & Resilience

### Service Failure Recovery
- [ ] LocalStack restart recovery
- [ ] WebSocket Gateway failure handling
- [ ] Step Functions Local restart recovery
- [ ] Lambda function error recovery
- [ ] DynamoDB connection error handling
- [ ] S3 access error handling

### Network Issues
- [ ] WebSocket connection loss recovery
- [ ] Intermittent network connectivity
- [ ] DNS resolution failures
- [ ] Port availability issues
- [ ] Firewall blocking recovery
- [ ] Proxy configuration handling

### Data Corruption Scenarios
- [ ] Invalid session data handling
- [ ] Corrupted message handling
- [ ] Malformed query processing
- [ ] Database constraint violations
- [ ] File system errors
- [ ] Missing dependency handling

### Timeout Management
- [ ] Lambda function timeouts
- [ ] Step Functions execution timeouts
- [ ] WebSocket message timeouts
- [ ] Database operation timeouts
- [ ] User interaction timeouts
- [ ] External service timeouts

### Error User Experience
- [ ] Clear error messages displayed
- [ ] Error recovery instructions provided
- [ ] System state preserved during errors
- [ ] Graceful degradation when possible
- [ ] Error logging for debugging
- [ ] User notification of service issues

---

## 🔒 Security Testing

### Input Validation
- [ ] Script injection prevention (`<script>alert('xss')</script>`)
- [ ] SQL injection prevention (`'; DROP TABLE sessions; --`)
- [ ] Command injection prevention (`; rm -rf /`)
- [ ] Path traversal prevention (`../../etc/passwd`)
- [ ] Large payload handling (>1MB messages)
- [ ] Special character handling
- [ ] Unicode character handling
- [ ] Binary data rejection

### Authentication Security
- [ ] Unauthenticated access prevention
- [ ] Invalid JWT token rejection
- [ ] Expired token handling
- [ ] Token tampering detection
- [ ] Session hijacking prevention
- [ ] CSRF protection (if applicable)
- [ ] Rate limiting (if implemented)

### Data Security
- [ ] Sensitive data not logged
- [ ] Session data encryption (if implemented)
- [ ] Secure token storage
- [ ] Database access controls
- [ ] S3 bucket security
- [ ] Secrets Manager access controls

### Network Security
- [ ] WebSocket connection security
- [ ] TLS/SSL configuration (if applicable)
- [ ] CORS policy compliance
- [ ] Origin validation
- [ ] Protocol upgrade security
- [ ] Man-in-the-middle protection

---

## 🔄 Integration Testing

### End-to-End User Journeys

#### Journey 1: First Time User
- [ ] Open application
- [ ] View authentication form
- [ ] Sign in with demo account
- [ ] See welcome message
- [ ] Send first query
- [ ] Receive response
- [ ] Ask follow-up question
- [ ] Sign out

#### Journey 2: Complex Analysis
- [ ] Authenticate
- [ ] Send complex causal query
- [ ] Provide clarification when requested
- [ ] Review analysis results
- [ ] Ask for explanation
- [ ] Request different analysis
- [ ] Compare results

#### Journey 3: Form-Based Analysis
- [ ] Authenticate
- [ ] Fill out structured form
- [ ] Submit analysis request
- [ ] Monitor execution
- [ ] Review detailed results
- [ ] Modify parameters
- [ ] Rerun analysis

#### Journey 4: Multi-Session Usage
- [ ] Start session 1
- [ ] Open session 2 (different browser/user)
- [ ] Run analyses in parallel
- [ ] Verify session isolation
- [ ] Close session 1
- [ ] Continue session 2
- [ ] Verify data integrity

### Cross-Component Integration
- [ ] Frontend ↔ WebSocket Gateway
- [ ] WebSocket Gateway ↔ Step Functions
- [ ] Step Functions ↔ Lambda Functions
- [ ] Lambda Functions ↔ DynamoDB
- [ ] Lambda Functions ↔ S3
- [ ] Lambda Functions ↔ Secrets Manager

### Service Dependency Testing
- [ ] Start services in different orders
- [ ] Handle missing dependencies gracefully
- [ ] Service discovery and health checks
- [ ] Dependency failure recovery
- [ ] Circular dependency prevention

---

## 📊 Monitoring & Observability

### Logging Verification
- [ ] Frontend logs captured
- [ ] WebSocket Gateway logs available
- [ ] Lambda function logs accessible
- [ ] Step Functions execution logs
- [ ] DynamoDB operation logs
- [ ] Error logs properly formatted

### Metrics Collection
- [ ] Performance metrics tracked
- [ ] Error rate monitoring
- [ ] User session metrics
- [ ] Resource utilization metrics
- [ ] Business logic metrics
- [ ] System health metrics

### Debugging Support
- [ ] Execution traces available
- [ ] State inspection possible
- [ ] Log correlation working
- [ ] Debug mode functionality
- [ ] Development tools integration

---

## 🚀 Deployment & Configuration

### Local Environment
- [ ] Docker Compose configuration correct
- [ ] Environment variables properly set
- [ ] Port mappings functional
- [ ] Volume mounts working
- [ ] Network connectivity between services
- [ ] Service startup order correct

### Configuration Management
- [ ] LocalStack services configured
- [ ] Lambda function deployment
- [ ] Step Functions state machine deployment
- [ ] DynamoDB table creation
- [ ] S3 bucket setup
- [ ] Cognito user pool configuration

### Cleanup & Reset
- [ ] Clean shutdown process
- [ ] Data persistence across restarts
- [ ] Reset to clean state capability
- [ ] Resource cleanup on shutdown
- [ ] No orphaned processes or data

---

## 📱 Browser Compatibility

### Desktop Browsers
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Mobile Browsers
- [ ] Chrome Mobile
- [ ] Safari iOS
- [ ] Samsung Internet
- [ ] Firefox Mobile

### Browser Features
- [ ] WebSocket support
- [ ] Local Storage functionality
- [ ] JavaScript ES6+ features
- [ ] CSS Grid/Flexbox support
- [ ] Responsive design

---

## 📋 Test Execution Tracking

### Test Run Information
- **Date**: ___________
- **Tester**: ___________
- **Environment**: Local Development
- **Version**: Sprint 1
- **Browser**: ___________

### Summary Results
- **Total Tests**: _____ / _____
- **Passed**: _____ ✅
- **Failed**: _____ ❌
- **Skipped**: _____ ⏸️
- **Pass Rate**: _____%

### Critical Issues Found
1. ________________________________
2. ________________________________
3. ________________________________

### Overall Status
- [ ] ✅ **READY FOR PRODUCTION** - All critical tests pass
- [ ] ⚠️ **READY WITH MINOR ISSUES** - Non-critical issues identified
- [ ] ❌ **NOT READY** - Critical issues must be resolved

### Sign-off
- **Tester Signature**: ___________
- **Date**: ___________
- **Approval**: ___________

---

## 🔧 Automated Test Scripts

For automated execution of this checklist, use the following scripts:

```bash
# Run basic health checks
./scripts/health-check.sh

# Run authentication tests
./scripts/test-auth.sh

# Run agent functionality tests
./scripts/test-agent.sh

# Run performance tests
./scripts/test-performance.sh

# Run security tests
./scripts/test-security.sh

# Generate test report
./scripts/generate-report.sh
```

---

*This checklist should be executed completely before any major release or deployment. All items should be verified and documented for traceability and compliance.*
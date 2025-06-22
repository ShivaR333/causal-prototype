# Sprint Documentation

## Sprint 1 - Cloud Architecture Simulation & Testing
**Start Date**: 2025-06-22  
**Sprint Counter**: 1

### Sprint Goals
1. Adapt current codebase to cloud-native architecture
2. Add basic authentication and session management
3. Create local cloud simulation environment
4. Implement core REACT loop with Lambda/ECS split

### Architecture Decisions

#### Function Split Strategy
- **Lambda Functions**: Agentic functions (LLM interactions, orchestration)
- **ECS/Fargate**: Analytics workloads (EDA, causal analysis)

#### Authentication Approach
- Simple Cognito user pools (email/password)
- JWT token validation
- Basic session management

#### Communication Protocol
- WebSocket with JSON messages
- No streaming in Sprint 1
- Synchronous request/response pattern

### Sprint 1 Scope

#### In Scope
1. **Basic Authentication**
   - Cognito user pool setup
   - Simple signup/login flow
   - JWT token validation

2. **Core Lambda Functions**
   - WebSocket handler
   - Parse initial query
   - Invoke LLM
   - Dispatch tool
   - Append output
   - Handle finish

3. **ECS Tasks**
   - EDA analysis container
   - Causal analysis container

4. **Session Management**
   - DynamoDB session storage
   - Basic context persistence

5. **Local Testing**
   - LocalStack setup
   - Basic integration tests

#### Out of Scope (Backlog)
1. **Advanced Authentication**
   - Multi-tenant support
   - API key authentication
   - SSO/SAML integration
   - Role-based access control

2. **Data Management**
   - File size limits
   - Data retention policies
   - Privacy/compliance features
   - Large file handling

3. **Advanced Features**
   - Streaming responses
   - WebSocket reconnection logic
   - Rate limiting
   - Usage analytics

4. **Production Features**
   - Monitoring/alerting
   - Cost optimization
   - Auto-scaling policies
   - Backup/disaster recovery

### Implementation Plan

#### Week 1: Infrastructure & Setup
- [x] Create local cloud docker-compose
- [ ] LocalStack setup scripts
- [ ] WebSocket gateway simulator
- [ ] Basic Lambda function structure

#### Week 2: Core Functions
- [ ] Split backend logic into Lambdas
- [ ] Implement Step Functions workflow
- [ ] ECS task definitions
- [ ] DynamoDB session table

#### Week 3: Authentication
- [ ] Cognito user pool setup
- [ ] Frontend auth components
- [ ] JWT validation middleware
- [ ] Protected routes

#### Week 4: Integration & Testing
- [ ] End-to-end workflow testing
- [ ] Error handling
- [ ] Documentation
- [ ] Demo preparation

### Technical Specifications

#### WebSocket Message Format
```json
{
  "action": "query|response|error",
  "sessionId": "uuid",
  "messageId": "uuid",
  "payload": {
    "type": "natural_language|structured",
    "content": "..."
  }
}
```

#### Lambda Function Interfaces
1. **parse-initial-query**
   - Input: User query + session context
   - Output: Structured query for LLM

2. **invoke-llm**
   - Input: Prompt + context
   - Output: LLM response with tool calls

3. **dispatch-tool**
   - Input: Tool name + parameters
   - Output: Tool selection for Step Functions

4. **append-output**
   - Input: Tool output
   - Output: Updated context

5. **handle-finish**
   - Input: Final response
   - Output: Formatted user response

#### ECS Task Specifications
1. **EDA Task**
   - Memory: 2GB
   - CPU: 1 vCPU
   - Timeout: 5 minutes

2. **Causal Analysis Task**
   - Memory: 4GB
   - CPU: 2 vCPU
   - Timeout: 10 minutes

### Progress Tracking

#### Completed
- [x] Architecture analysis
- [x] Sprint planning
- [x] Local cloud docker-compose
- [x] Project structure setup
- [x] LocalStack setup scripts
- [x] WebSocket gateway simulator
- [x] Lambda function implementation
- [x] Step Functions workflow
- [x] Authentication integration
- [x] Frontend updates

#### In Progress
- [ ] ECS task definitions
- [ ] Integration testing

#### Pending
- [ ] S3 file storage abstraction
- [ ] Unit tests with moto
- [ ] End-to-end testing
- [ ] Documentation updates

### Risk Mitigation
1. **Complexity**: Start with minimal viable architecture
2. **Testing**: Use mocks for external services initially
3. **Performance**: Profile Lambda cold starts early
4. **Integration**: Test each component in isolation first

### Local Development Hacks & Production Requirements

#### 🚨 CRITICAL: Local Development Workarounds for Production Migration

The following changes were made for local development that **MUST** be addressed before production deployment:

#### 1. WebSocket Gateway Authentication Bypass
**File**: `local-cloud/websocket-gateway/server.js`
**Hack**: Added authentication bypass for tokens containing 'local-dev'
```javascript
// HACK: Local development bypass - REMOVE IN PRODUCTION
if (token && token.includes('local-dev')) {
  logger.info('Using local development authentication bypass');
  return {
    userId: 'local-user',
    email: 'user@localhost'
  };
}
```
**Production Fix Required**: 
- Remove the bypass logic
- Ensure proper JWT secrets are configured in AWS Secrets Manager
- Implement proper Cognito integration for token validation

#### 2. Frontend WebSocket Authentication
**File**: `frontend/src/lib/websocket.ts`
**Hack**: Using hardcoded 'local-dev-token-bypass' instead of real JWT
```javascript
// HACK: Using bypass token for local dev
authToken = 'local-dev-token-bypass';
```
**Production Fix Required**:
- Integrate with actual Cognito authentication
- Use real JWT tokens from authenticated users
- Implement proper token refresh logic

#### 3. Docker Port Exposures
**File**: `docker-compose.local-cloud.yml`
**Hack**: Exposed internal service ports to localhost for development
```yaml
# HACK: Exposed for local development - should be internal in production
ports:
  - "8000:8000"  # EDA Simulator API
  - "8080:8080"  # WebSocket Gateway
```
**Production Fix Required**:
- Remove port exposures - services should communicate internally
- Use proper AWS networking (VPC, security groups)
- API Gateway should be the only public entry point

#### 4. Environment Configuration
**File**: `frontend/.env.local`
**Hack**: Hardcoded localhost URLs
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8080
```
**Production Fix Required**:
- Use environment-specific URLs
- Configure proper API Gateway WebSocket endpoints
- Use HTTPS/WSS for all communications

#### 5. AWS Service Mocking
**Current State**: All AWS services running through LocalStack
**Production Migration Required**:
- Replace LocalStack endpoints with real AWS services
- Configure proper IAM roles and policies
- Set up real DynamoDB tables, S3 buckets, Step Functions
- Configure Cognito User Pools
- Set up proper Secrets Manager secrets

#### 6. Error Handling & Security
**Missing for Production**:
- Proper error handling for authentication failures
- Rate limiting and DDoS protection
- Input validation and sanitization
- Proper logging and monitoring
- CORS configuration for production domains

#### Production Deployment Checklist
- [ ] Remove all authentication bypasses
- [ ] Configure real Cognito User Pool
- [ ] Set up proper JWT secrets in AWS Secrets Manager
- [ ] Configure API Gateway with WebSocket support
- [ ] Set up VPC and security groups
- [ ] Implement proper IAM roles
- [ ] Configure production environment variables
- [ ] Set up monitoring and alerting
- [ ] Implement proper error handling
- [ ] Add rate limiting and security headers
- [ ] Configure HTTPS/WSS endpoints
- [ ] Test with real AWS services

#### Security Notes
⚠️ **NEVER deploy these local development bypasses to production**
⚠️ **All hardcoded tokens and bypasses are security vulnerabilities in production**
⚠️ **Review and audit all authentication code before production deployment**

---

*Last updated: 2025-06-22*
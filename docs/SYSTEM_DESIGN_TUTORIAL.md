# Causal Analysis Agent - System Design & Testing Tutorial

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Components](#architecture-components)
3. [Data Flow & Communication](#data-flow--communication)
4. [Local Development Setup](#local-development-setup)
5. [Testing Guide](#testing-guide)
6. [Troubleshooting](#troubleshooting)
7. [Development Workflows](#development-workflows)

## System Overview

The Causal Analysis Agent is a cloud-native application that provides intelligent causal analysis through a conversational interface. The system uses AWS services to create a scalable, serverless architecture with real-time communication capabilities.

### Key Features
- **Real-time WebSocket Communication**: Bidirectional messaging between client and agent
- **Intelligent Agent Loop**: REACT (Reason-Act-Observe) pattern for complex analysis workflows
- **Serverless Architecture**: Lambda functions for lightweight operations, ECS for heavy computation
- **Session Management**: Persistent conversation context across interactions
- **Authentication**: Simple Cognito-based user management
- **Local Development**: Complete AWS simulation using LocalStack

### Target Cloud Architecture
```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Frontend  │────│   WebSocket  │────│  Step Functions │
│  (Next.js)  │    │   Gateway    │    │   (REACT Loop)  │
└─────────────┘    └──────────────┘    └─────────────────┘
                            │                      │
                            │                      ▼
                   ┌────────────────┐    ┌─────────────────┐
                   │   DynamoDB     │    │    Lambda       │
                   │  (Sessions)    │    │  Functions      │
                   └────────────────┘    └─────────────────┘
                                                  │
                                                  ▼
                                        ┌─────────────────┐
                                        │   ECS/Fargate   │
                                        │   (Analytics)   │
                                        └─────────────────┘
```

## Architecture Components

### 1. Frontend Layer (Next.js)

**Purpose**: User interface for interacting with the causal analysis agent

**Key Components**:
- `src/app/page.tsx` - Main application with chat interface
- `src/components/AuthForm.tsx` - Authentication UI
- `src/lib/websocket.ts` - WebSocket client for real-time communication
- `src/lib/auth.ts` - Authentication service with Cognito integration

**Responsibilities**:
- User authentication and session management
- Real-time messaging via WebSocket
- Form-based causal analysis queries
- Response visualization and interaction

### 2. WebSocket Gateway

**Purpose**: Manages real-time bidirectional communication between clients and the agent workflow

**Location**: `local-cloud/websocket-gateway/server.js`

**Key Features**:
- Connection management with authentication
- Message routing to Step Functions
- Session tracking and context persistence
- Error handling and reconnection logic

**Message Protocol**:
```json
{
  "action": "query|response|auth|prompt|error",
  "sessionId": "uuid",
  "messageId": "uuid", 
  "payload": {
    "type": "natural_language|structured",
    "content": "user message or response"
  }
}
```

### 3. Step Functions (REACT Loop Orchestration)

**Purpose**: Orchestrates the agent's reasoning and action workflow

**Location**: `local-cloud/step-functions/agent-workflow.json`

**Workflow States**:
1. **ParseInitialQuery** - Process and understand user input
2. **InvokeLLM** - Generate responses and determine next actions
3. **CheckResponse** - Route based on LLM output type
4. **DispatchTool** - Select and configure analysis tools
5. **RunEDATask/RunCausalAnalysisTask** - Execute heavy computations
6. **AppendToolOutput** - Update conversation context
7. **SendPrompt** - Request clarification from user
8. **HandleFinish** - Format and send final response

**Decision Points**:
- Tool selection (EDA vs Causal Analysis vs Data Query)
- User interaction needs (clarification vs completion)
- Error handling and recovery

### 4. Lambda Functions (Agentic Operations)

Lambda functions handle lightweight, stateless operations in the agent workflow:

#### 4.1 parse-initial-query
- **Purpose**: Parse user input and prepare context for LLM
- **Input**: User query, session context
- **Output**: Structured prompt for LLM
- **Location**: `local-cloud/lambdas/parse-initial-query/`

#### 4.2 invoke-llm
- **Purpose**: Call LLM service and interpret responses
- **Features**: Mock mode for testing, structured JSON responses
- **Input**: Prepared prompt, conversation history
- **Output**: Tool calls, clarification needs, or final answers

#### 4.3 dispatch-tool
- **Purpose**: Route tool execution based on LLM decisions
- **Input**: Tool name and parameters
- **Output**: Configured parameters for ECS tasks or Lambda execution

#### 4.4 append-tool-output
- **Purpose**: Update conversation context with tool results
- **Input**: Tool execution results
- **Output**: Updated context and next prompt

#### 4.5 send-prompt
- **Purpose**: Send clarification requests to users
- **Features**: WebSocket callback integration
- **Input**: Prompt text, session ID
- **Output**: Waits for user response via callback

#### 4.6 handle-finish
- **Purpose**: Format and send final responses
- **Input**: LLM final response
- **Output**: Formatted user message

#### 4.7 Error Handlers
- **handle-error**: Process workflow errors
- **handle-timeout**: Manage timeout scenarios
- **websocket-handler**: API Gateway WebSocket routing

### 5. ECS/Fargate (Heavy Computation)

**Purpose**: Execute compute-intensive analysis tasks

**Planned Tasks**:
- **EDA Analysis**: Exploratory data analysis with visualization
- **Causal Analysis**: Statistical causal inference methods
- **Data Processing**: Large dataset transformations

**Configuration**:
- **EDA Task**: 2GB memory, 1 vCPU, 5-minute timeout
- **Causal Analysis Task**: 4GB memory, 2 vCPU, 10-minute timeout

### 6. Data Layer

#### 6.1 DynamoDB Tables

**Sessions Table** (`causal-analysis-dev-sessions`):
```json
{
  "sessionId": "primary-key",
  "userId": "string",
  "context": {
    "history": [],
    "lastQuery": "string",
    "pendingTaskToken": "string"
  },
  "timestamp": "number",
  "createdAt": "number",
  "updatedAt": "number"
}
```

**Connections Table** (`causal-analysis-dev-connections`):
```json
{
  "connectionId": "primary-key",
  "userId": "string",
  "connectedAt": "number",
  "ttl": "number"
}
```

**Jobs Table** (`causal-analysis-dev-jobs`):
```json
{
  "jobId": "primary-key",
  "sessionId": "string",
  "tool": "string",
  "parameters": "object",
  "status": "dispatched|running|completed|failed",
  "createdAt": "number",
  "completedAt": "number",
  "ttl": "number"
}
```

#### 6.2 S3 Buckets

**Raw Data** (`causal-analysis-dev-rawdata`):
- Input datasets for analysis
- User-uploaded files
- Sample data for testing

**Artifacts** (`causal-analysis-dev-artifacts`):
- Analysis results and outputs
- Generated visualizations
- Temporary processing files

#### 6.3 Secrets Manager

**API Keys** (`causal-analysis-dev-api-key`):
- OpenAI API key
- Anthropic API key
- Other service credentials

**JWT Secret** (`causal-analysis-dev-jwt-secret`):
- Token signing secret
- Algorithm configuration
- Expiration settings

### 7. Authentication (Cognito)

**User Pool**: Simple email/password authentication
**Test Users**:
- `admin@example.com` / `AdminPass123!`
- `user@example.com` / `UserPass123!`

**Features**:
- JWT token-based authentication
- Session persistence
- Local development mock mode

## Data Flow & Communication

### 1. Authentication Flow
```
1. User opens application
2. AuthForm component renders
3. User enters credentials
4. AuthService calls Cognito (or mock in dev)
5. JWT tokens stored locally
6. WebSocket connection established
7. WebSocket authentication with JWT
8. Session created in DynamoDB
```

### 2. Query Processing Flow
```
1. User submits query via MessageInput
2. WebSocket sends query to gateway
3. Gateway starts Step Functions execution
4. ParseInitialQuery processes input
5. InvokeLLM generates response/tool calls
6. If tool needed:
   a. DispatchTool configures parameters
   b. ECS task executes analysis
   c. AppendToolOutput updates context
   d. Loop back to InvokeLLM
7. If clarification needed:
   a. SendPrompt requests user input
   b. User responds via WebSocket
   c. Continue processing
8. HandleFinish sends final response
9. Frontend displays result
```

### 3. Real-time Communication
```
Frontend ←─── WebSocket ───→ Gateway ←─── Step Functions
    │                           │              │
    │                           ▼              ▼
    └─── Auth ←─── Cognito  DynamoDB ←─── Lambda Functions
```

## Local Development Setup

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Git
- 8GB+ RAM recommended

### Step 1: Clone and Navigate
```bash
git clone <repository-url>
cd causal-prototype
```

### Step 2: Environment Configuration

Create environment file for LocalStack:
```bash
# Create .env file in project root
cat > .env << EOF
# LocalStack Configuration
LOCALSTACK_AUTH_TOKEN=your-token-here
DEBUG=1

# Application Configuration
OPENAI_API_KEY=test-key-for-local-dev
MOCK_LLM=true
NODE_ENV=development
EOF
```

### Step 3: Start Local Cloud Infrastructure

```bash
# Start all services
docker-compose -f docker-compose.local-cloud.yml up -d

# Check service status
docker-compose -f docker-compose.local-cloud.yml ps
```

Expected services:
- `localstack` - AWS services simulation
- `stepfunctions-local` - Workflow orchestration
- `dynamodb-admin` - Database management UI
- `websocket-gateway` - Real-time communication
- `frontend` - Next.js application

### Step 4: Initialize AWS Resources

```bash
# Run setup scripts
docker-compose -f docker-compose.local-cloud.yml run aws-cli /scripts/create-resources.sh

# Verify resources created
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal s3 ls
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal dynamodb list-tables
```

### Step 5: Deploy Lambda Functions

```bash
# Deploy all Lambda functions
docker-compose -f docker-compose.local-cloud.yml run aws-cli /scripts/deploy-lambdas.sh

# Verify deployment
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal lambda list-functions
```

### Step 6: Access Applications

- **Frontend**: http://localhost:3000
- **WebSocket Gateway**: ws://localhost:8080
- **DynamoDB Admin**: http://localhost:8001
- **LocalStack Dashboard**: http://localhost:4566
- **Step Functions Local**: http://localhost:8083

## Testing Guide

### Test 1: Authentication Flow

1. **Access Application**:
   ```
   Open http://localhost:3000
   ```

2. **Sign In**:
   - Click "Use Demo Account" or enter:
   - Email: `admin@example.com`
   - Password: `AdminPass123!`

3. **Verify Connection**:
   - Should see "Connected via WebSocket" in header
   - Session ID should appear (last 8 characters)

4. **Expected Results**:
   - Authentication successful message
   - WebSocket connection established
   - Session created in DynamoDB

### Test 2: Basic Query Processing

1. **Send Natural Language Query**:
   ```
   Type: "What's the effect of discount on sales?"
   ```

2. **Monitor Workflow**:
   - Check Step Functions execution at http://localhost:8083
   - Monitor Lambda logs in Docker
   - Watch DynamoDB updates at http://localhost:8001

3. **Expected Flow**:
   - Query parsed by `parse-initial-query`
   - LLM mock response from `invoke-llm`
   - Tool dispatch to causal analysis
   - Final response with mock results

4. **Expected Response**:
   ```
   Mock causal analysis results showing:
   - Treatment: discount
   - Outcome: sales
   - Method: linear_regression
   - Estimated effect and confidence interval
   ```

### Test 3: Clarification Flow

1. **Send Ambiguous Query**:
   ```
   Type: "Analyze my data"
   ```

2. **Expected Behavior**:
   - Agent requests clarification
   - Input box switches to "Respond" mode
   - Yellow highlight indicates prompt mode

3. **Provide Clarification**:
   ```
   Type: "I want to see the effect of price on demand"
   ```

4. **Verify Processing**:
   - Normal query processing resumes
   - Analysis results returned

### Test 4: Error Handling

1. **Trigger Error**:
   - Stop one of the services:
   ```bash
   docker stop causal-prototype-stepfunctions-local-1
   ```

2. **Send Query**:
   ```
   Type: "Test error handling"
   ```

3. **Expected Behavior**:
   - Error message displayed
   - User notified of service unavailability
   - Connection status updated

4. **Recovery Test**:
   ```bash
   # Restart service
   docker-compose -f docker-compose.local-cloud.yml up stepfunctions-local -d
   ```

### Test 5: Session Persistence

1. **Create Session**:
   - Send a query and get response
   - Note the session ID

2. **Refresh Browser**:
   - Should automatically reconnect
   - Session ID should remain the same

3. **Send Follow-up**:
   ```
   Type: "What was my previous query?"
   ```

4. **Expected Result**:
   - Agent should reference previous context
   - Conversation history maintained

### Test 6: Structured Form Query

1. **Use Causal Analysis Form**:
   - Fill in form on right sidebar:
     - Treatment: `discount_offer`
     - Outcome: `purchase_amount`
     - Confounders: `customer_age,customer_income`
     - Data File: `sample_data/eCommerce_sales.csv`

2. **Submit Form**:
   - Click "Run Analysis"

3. **Expected Flow**:
   - Structured query processed
   - Same Step Functions workflow
   - Formatted results displayed

### Test 7: Multiple User Sessions

1. **Open Incognito Window**:
   - Navigate to http://localhost:3000
   - Sign in as `user@example.com` / `UserPass123!`

2. **Send Queries from Both Sessions**:
   - Verify independent session handling
   - Check DynamoDB for separate session records

3. **Monitor Connections**:
   - Use DynamoDB Admin to view connections table
   - Should see multiple active connections

## Debugging and Monitoring

### Service Logs

```bash
# View all logs
docker-compose -f docker-compose.local-cloud.yml logs

# Specific service logs
docker-compose -f docker-compose.local-cloud.yml logs websocket-gateway
docker-compose -f docker-compose.local-cloud.yml logs localstack
docker-compose -f docker-compose.local-cloud.yml logs frontend
```

### Lambda Function Logs

```bash
# View Lambda execution logs
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal logs describe-log-groups

# Get specific function logs
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal logs get-log-events --log-group-name /aws/lambda/causal-analysis-dev-invoke-llm
```

### Database Inspection

1. **DynamoDB Admin**: http://localhost:8001
   - View sessions, connections, jobs tables
   - Monitor real-time updates during queries

2. **AWS CLI Access**:
   ```bash
   # Query sessions
   docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal dynamodb scan --table-name causal-analysis-dev-sessions
   
   # Query connections
   docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal dynamodb scan --table-name causal-analysis-dev-connections
   ```

### Step Functions Monitoring

1. **Access Step Functions Local**: http://localhost:8083
2. **Monitor Executions**:
   - View execution history
   - Inspect state transitions
   - Debug failed executions

### WebSocket Testing

Use browser developer tools or a WebSocket client:

```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8080');
ws.onmessage = (event) => console.log('Received:', JSON.parse(event.data));
ws.send(JSON.stringify({
  action: 'auth',
  payload: { token: 'test-token', userId: 'test-user' }
}));
```

## Troubleshooting

### Common Issues

#### 1. Services Not Starting
```bash
# Check Docker resources
docker system df
docker system prune  # if needed

# Restart specific service
docker-compose -f docker-compose.local-cloud.yml restart localstack
```

#### 2. LocalStack Connection Errors
```bash
# Check LocalStack status
curl http://localhost:4566/_localstack/health

# Restart LocalStack
docker-compose -f docker-compose.local-cloud.yml restart localstack

# Re-run setup scripts
docker-compose -f docker-compose.local-cloud.yml run aws-cli /scripts/create-resources.sh
```

#### 3. WebSocket Connection Failed
```bash
# Check gateway logs
docker-compose -f docker-compose.local-cloud.yml logs websocket-gateway

# Verify port availability
netstat -an | grep 8080

# Restart gateway
docker-compose -f docker-compose.local-cloud.yml restart websocket-gateway
```

#### 4. Lambda Function Errors
```bash
# Check function exists
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal lambda list-functions

# Redeploy functions
docker-compose -f docker-compose.local-cloud.yml run aws-cli /scripts/deploy-lambdas.sh

# Check execution role
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal iam get-role --role-name lambda-execution-role
```

#### 5. Frontend Not Loading
```bash
# Check frontend service
docker-compose -f docker-compose.local-cloud.yml logs frontend

# Restart frontend
docker-compose -f docker-compose.local-cloud.yml restart frontend

# Check environment variables
docker-compose -f docker-compose.local-cloud.yml exec frontend env
```

### Performance Issues

#### Memory Usage
```bash
# Monitor container resources
docker stats

# If high memory usage, restart heavy services
docker-compose -f docker-compose.local-cloud.yml restart localstack stepfunctions-local
```

#### Network Issues
```bash
# Check network connectivity
docker-compose -f docker-compose.local-cloud.yml exec frontend ping localstack
docker-compose -f docker-compose.local-cloud.yml exec websocket-gateway ping stepfunctions-local
```

## Development Workflows

### Adding New Lambda Functions

1. **Create Function Directory**:
   ```bash
   mkdir local-cloud/lambdas/my-new-function
   cd local-cloud/lambdas/my-new-function
   ```

2. **Create Function Code**:
   ```python
   # index.py
   def handler(event, context):
       return {"statusCode": 200, "body": "Hello World"}
   ```

3. **Add Requirements**:
   ```bash
   # requirements.txt
   boto3==1.28.85
   ```

4. **Update Deployment Script**:
   ```bash
   # Add to local-cloud/setup-scripts/deploy-lambdas.sh
   create_lambda "my-new-function" "index.handler" "python3.9" 30 256
   ```

5. **Deploy and Test**:
   ```bash
   docker-compose -f docker-compose.local-cloud.yml run aws-cli /scripts/deploy-lambdas.sh
   ```

### Modifying Step Functions Workflow

1. **Edit Workflow Definition**:
   ```bash
   # Modify local-cloud/step-functions/agent-workflow.json
   ```

2. **Update State Machine**:
   ```bash
   docker-compose -f docker-compose.local-cloud.yml run aws-cli /scripts/create-state-machine.sh
   ```

3. **Test New Workflow**:
   - Send test query through frontend
   - Monitor execution at http://localhost:8083

### Frontend Development

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Run Development Server**:
   ```bash
   npm run dev
   ```

3. **Test Changes**:
   - Frontend runs on http://localhost:3000
   - Hot reload enabled for rapid development

### Testing Individual Components

#### Lambda Function Testing
```bash
# Test individual function
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal lambda invoke \
  --function-name causal-analysis-dev-parse-initial-query \
  --payload '{"sessionId":"test","query":{"type":"natural_language","content":"test query"}}' \
  response.json

cat response.json
```

#### WebSocket Gateway Testing
```bash
# Test WebSocket connection
npm install -g wscat
wscat -c ws://localhost:8080

# Send test message
{"action":"auth","payload":{"token":"test","userId":"test"}}
```

#### Step Functions Testing
```bash
# Start execution manually
docker-compose -f docker-compose.local-cloud.yml run aws-cli awslocal stepfunctions start-execution \
  --state-machine-arn arn:aws:states:us-east-1:000000000000:stateMachine:causal-analysis-dev-agent-sm \
  --input '{"sessionId":"test","query":{"type":"natural_language","content":"test"}}'
```

This comprehensive tutorial provides everything needed to understand, set up, and test the Causal Analysis Agent system. The modular architecture and extensive testing capabilities make it ideal for rapid development and validation of cloud-native AI applications.
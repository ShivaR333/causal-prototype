# Quick Start Guide - Causal Analysis Agent

## 🚀 Get Running in 10 Minutes

This guide gets you up and running with the local cloud simulation environment quickly.

## Prerequisites

- Docker Desktop with 8GB+ RAM
- 10GB free disk space
- Ports 3000, 4566, 8001, 8080, 8083 available

## Step 1: Start Services (2 minutes)

```bash
# Clone and navigate to project
git clone <repository-url>
cd causal-prototype

# Start all services
docker-compose -f docker-compose.local-cloud.yml up -d

# Wait for services to start (watch logs)
docker-compose -f docker-compose.local-cloud.yml logs -f
```

**Wait for**: `LocalStack is ready` message

## Step 2: Initialize Cloud Resources (2 minutes)

```bash
# Run setup scripts
docker-compose -f docker-compose.local-cloud.yml run aws-cli /scripts/create-resources.sh
```

**Expected output**:
```
✅ S3 buckets created
✅ DynamoDB tables created  
✅ Cognito user pool created
✅ Lambda functions deployed
✅ Step Functions state machine created
```

## Step 3: Test the Application (5 minutes)

### 3.1 Access Frontend
Open http://localhost:3000

### 3.2 Sign In
- Click **"Use Demo Account"**
- Or enter manually:
  - Email: `admin@example.com`
  - Password: `AdminPass123!`

### 3.3 Verify Connection
You should see:
```
🟢 Connected via WebSocket • Session: abc12345
```

### 3.4 Test Basic Query
Type in the chat:
```
What's the effect of discount on sales?
```

**Expected response**:
```
✅ Causal Analysis Complete

Estimated Effect: 0.2450
95% Confidence Interval: [0.1823, 0.3077]
Method: linear_regression
```

### 3.5 Test Clarification Flow
Type:
```
Analyze my data
```

You should get a clarification prompt. Respond with:
```
I want to see the effect of price on demand
```

## Step 4: Explore Features (Optional)

### Test Structured Form
1. Use the **Causal Analysis** form on the right
2. Fill in:
   - Treatment: `discount_offer`
   - Outcome: `purchase_amount`
   - Confounders: `customer_age,customer_income`
3. Click **"Run Analysis"**

### Monitor System
- **DynamoDB Admin**: http://localhost:8001
- **Step Functions**: http://localhost:8083
- **LocalStack Health**: http://localhost:4566/_localstack/health

## Quick Troubleshooting

### Services Won't Start
```bash
# Check Docker resources
docker system df

# Restart specific service
docker-compose -f docker-compose.local-cloud.yml restart localstack
```

### Can't Connect to WebSocket
```bash
# Check gateway logs
docker-compose -f docker-compose.local-cloud.yml logs websocket-gateway

# Restart gateway
docker-compose -f docker-compose.local-cloud.yml restart websocket-gateway
```

### Authentication Failed
```bash
# Re-create Cognito resources
docker-compose -f docker-compose.local-cloud.yml run aws-cli /scripts/create-cognito.sh
```

### Lambda Errors
```bash
# Redeploy functions
docker-compose -f docker-compose.local-cloud.yml run aws-cli /scripts/deploy-lambdas.sh
```

## Understanding the Flow

1. **Frontend** (Next.js) → **WebSocket Gateway** (Node.js)
2. **WebSocket Gateway** → **Step Functions** (Workflow orchestration)
3. **Step Functions** → **Lambda Functions** (Agent logic)
4. **Lambda Functions** → **DynamoDB** (Session storage)
5. **Response** flows back through the same chain

## Key Components

- **LocalStack**: Simulates AWS services locally
- **WebSocket Gateway**: Real-time communication hub
- **Step Functions**: Orchestrates the REACT agent loop
- **Lambda Functions**: Handle agent reasoning and actions
- **DynamoDB**: Stores session and conversation data
- **Frontend**: React/Next.js chat interface

## Next Steps

For detailed system understanding, see:
- [System Design Tutorial](./SYSTEM_DESIGN_TUTORIAL.md) - Complete architecture guide
- [Sprint Documentation](../SprintDoc.md) - Current development status
- [Local Cloud README](../local-cloud/README.md) - Development workflows

## Test Scenarios

### Scenario 1: Basic Causal Query
```
Input: "What's the effect of education on income?"
Expected: Structured causal analysis with effect size
```

### Scenario 2: Exploratory Analysis
```
Input: "Show me insights about the ecommerce data"
Expected: EDA task dispatch and summary
```

### Scenario 3: Interactive Clarification
```
Input: "Run analysis"
Expected: Clarification request
Follow-up: "Effect of discount on purchase amount"
Expected: Structured analysis
```

### Scenario 4: Error Handling
```
Stop service: docker stop causal-prototype-stepfunctions-local-1
Input: "Test query"
Expected: Error message with fallback
```

That's it! You now have a fully functional causal analysis agent running locally with complete AWS cloud simulation. 🎉
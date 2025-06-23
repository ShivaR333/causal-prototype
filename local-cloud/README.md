# Local Cloud Simulation Environment

This directory contains the components needed to simulate the AWS cloud architecture locally.

## Directory Structure

```
local-cloud/
├── README.md                    # This file
├── lambdas/                     # Lambda function implementations
│   ├── parse-initial-query/
│   ├── invoke-llm/
│   ├── dispatch-tool/
│   ├── send-prompt/
│   ├── append-tool-output/
│   ├── handle-finish/
│   └── websocket-handler/
├── websocket-gateway/           # WebSocket API Gateway simulator
│   ├── Dockerfile
│   ├── package.json
│   └── server.js
├── setup-scripts/               # LocalStack initialization scripts
│   ├── create-resources.sh
│   ├── create-tables.sh
│   ├── create-buckets.sh
│   ├── create-secrets.sh
│   └── create-cognito.sh
├── step-functions/              # Step Functions definitions
│   └── agent-workflow.json
├── tests/                       # Local cloud tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── config/                      # Configuration files
    ├── localstack.env
    ├── sam-local.yaml
    └── test-data/
```

## Quick Start

1. **Start the local cloud environment:**
   ```bash
   docker-compose -f docker-compose.local-cloud.yml up -d
   ```

2. **Initialize AWS resources:**
   ```bash
   docker-compose -f docker-compose.local-cloud.yml run aws-cli /scripts/create-resources.sh
   ```

3. **Deploy Lambda functions:**
   ```bash
   cd lambdas
   sam local start-lambda --docker-network causal-prototype_causal-cloud
   ```

4. **Start Step Functions Local:**
   ```bash
   # Already started in docker-compose
   # Access at http://localhost:8083
   ```

5. **Run tests:**
   ```bash
   pytest tests/ --localstack
   ```

## Development Workflow

### Adding a New Lambda Function

1. Create directory: `lambdas/function-name/`
2. Add `index.py` with handler
3. Add `requirements.txt` for dependencies
4. Update SAM template
5. Test locally with SAM CLI

### Testing WebSocket Communication

1. Connect to `ws://localhost:8080`
2. Send test messages
3. Monitor Lambda invocations
4. Check DynamoDB for session data

### Debugging Step Functions

1. Access Step Functions Local UI at http://localhost:8083
2. Start execution with test input
3. Monitor state transitions
4. Check CloudWatch logs in LocalStack

## Environment Variables

### LocalStack Services
- `SERVICES`: Comma-separated list of AWS services
- `LAMBDA_EXECUTOR`: Use 'docker' for Lambda containers
- `DEBUG`: Enable debug logging

### Application Configuration
- `WEBSOCKET_URL`: WebSocket endpoint
- `COGNITO_ENDPOINT`: Authentication service
- `S3_ENDPOINT`: Object storage
- `DYNAMODB_ENDPOINT`: Session storage

## Testing Strategy

### Unit Tests (pytest + moto)
```python
import boto3
from moto import mock_s3, mock_dynamodb

@mock_s3
def test_s3_upload():
    # Test S3 operations
    pass

@mock_dynamodb
def test_session_storage():
    # Test DynamoDB operations
    pass
```

### Integration Tests (LocalStack)
```python
import pytest
from localstack_client.session import Session

@pytest.fixture
def localstack():
    session = Session()
    return session.client('s3')

def test_full_workflow(localstack):
    # Test complete workflow
    pass
```

### End-to-End Tests
- Full user journey from WebSocket connection
- Authentication flow
- Analysis request and response
- Result retrieval

## Troubleshooting

### Common Issues

1. **LocalStack not starting**
   - Check Docker daemon is running
   - Verify port availability
   - Check Docker socket mounting

2. **Lambda timeouts**
   - Increase timeout in SAM template
   - Check network connectivity
   - Verify endpoint configuration

3. **Step Functions failures**
   - Check Lambda function logs
   - Verify IAM permissions
   - Check state machine definition

### Debugging Commands

```bash
# View LocalStack logs
docker logs causal-prototype-localstack-1

# List Lambda functions
awslocal lambda list-functions

# Describe DynamoDB tables
awslocal dynamodb list-tables

# Check S3 buckets
awslocal s3 ls
```

## Next Steps

1. Implement Lambda functions
2. Create WebSocket gateway
3. Set up authentication flow
4. Add monitoring and logging
5. Create CI/CD pipeline
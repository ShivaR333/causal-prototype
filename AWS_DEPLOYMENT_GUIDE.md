# AWS Deployment Guide for Causal Analysis Platform

This guide provides step-by-step instructions for deploying the Causal Analysis Platform to AWS.

## Prerequisites

Before starting the deployment, ensure you have:

1. **AWS CLI installed and configured**
   ```bash
   aws --version
   aws configure
   ```

2. **Terraform installed**
   ```bash
   terraform --version
   ```

3. **Python 3.9+ and pip installed**
   ```bash
   python3 --version
   pip --version
   ```

4. **OpenAI API Key** (for LLM integration)

## Quick Deployment (Automated)

The easiest way to deploy is using the automated deployment script:

```bash
# Clone and navigate to the project
cd causal-prototype

# Run the automated deployment script
./scripts/deploy-to-aws.sh
```

This script will:
- ✅ Check all prerequisites
- 📦 Package Lambda functions
- 🐳 Build and push Docker containers to ECR
- 🏗️ Create S3 bucket for Terraform state
- 🚀 Deploy infrastructure with Terraform
- 📁 Upload sample data to S3
- 🧪 Test the deployment

## Manual Deployment Steps

If you prefer manual control or the automated script fails, follow these steps:

### Step 1: Environment Setup

1. **Copy Terraform configuration**
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit `terraform.tfvars` file with your values**
   ```bash
   # Required: Add your OpenAI API key
   openai_api_key = "sk-your-actual-openai-api-key-here"
   
   # Optional: Customize other settings
   project_name = "causal-analysis"
   environment  = "dev"
   openai_model = "gpt-3.5-turbo"
   ```

   **Important**: The OpenAI API key will be securely stored in AWS Secrets Manager during deployment.

### Step 2: Package Lambda Functions

```bash
# Make the packaging script executable
chmod +x scripts/package-lambdas.sh

# Package all Lambda functions
./scripts/package-lambdas.sh
```

This creates ZIP files in the `lambda-packages/` directory for all Lambda functions.

### Step 3: Build and Push Container Images

```bash
# Make the container build script executable
chmod +x scripts/build-and-push-containers.sh

# Build and push Docker images to ECR
./scripts/build-and-push-containers.sh
```

This will:
- Create ECR repositories for EDA and Analysis services
- Build Docker images from `backend/Dockerfile.eda` and `backend/Dockerfile.analysis`
- Push images to ECR with latest and timestamped tags

### Step 4: Setup Terraform Backend

1. **Create S3 bucket for Terraform state**
   ```bash
   # Replace with a unique bucket name
   BUCKET_NAME="terraform-state-bucket-$(date +%s)"
   aws s3 mb "s3://$BUCKET_NAME" --region me-south-1
   
   # Enable versioning
   aws s3api put-bucket-versioning \
     --bucket "$BUCKET_NAME" \
     --versioning-configuration Status=Enabled
   ```

2. **Update Terraform configuration**
   ```bash
   # Edit terraform/main.tf and replace the bucket name
   sed -i.bak "s/terraform-state-bucket/$BUCKET_NAME/g" terraform/main.tf
   ```

### Step 5: Deploy Infrastructure

```bash
cd terraform

# Initialize Terraform
terraform init

# Review the deployment plan
terraform plan

# Deploy the infrastructure
terraform apply

# Save outputs for reference
terraform output > ../terraform-outputs.txt
```

### Step 6: Upload Sample Data

```bash
cd ..

# Get the S3 bucket name from Terraform outputs
RAWDATA_BUCKET=$(grep "rawdata_bucket_name" terraform-outputs.txt | cut -d'"' -f4)

# Upload sample data
aws s3 sync data/sample_data/ "s3://$RAWDATA_BUCKET/sample_data/"

# Upload DAG configurations
aws s3 sync backend/causal_analysis/config/ "s3://$RAWDATA_BUCKET/config/"
```

### Step 7: Update Frontend Configuration

1. **Get deployment outputs**
   ```bash
   # Get WebSocket API endpoint
   WEBSOCKET_URL=$(terraform output -raw api_gateway_websocket_url)
   
   # Get Cognito configuration
   USER_POOL_ID=$(terraform output -raw user_pool_id)
   USER_POOL_CLIENT_ID=$(terraform output -raw user_pool_client_id)
   ```

2. **Update environment configuration**
   Create `.env.local` in the frontend directory:
   ```bash
   cd frontend
   echo "NEXT_PUBLIC_WEBSOCKET_URL=$WEBSOCKET_URL" > .env.local
   echo "NEXT_PUBLIC_USER_POOL_ID=$USER_POOL_ID" >> .env.local
   echo "NEXT_PUBLIC_USER_POOL_CLIENT_ID=$USER_POOL_CLIENT_ID" >> .env.local
   ```

## Infrastructure Components

The deployment creates:

- **Lambda Functions**: 11 functions including WebSocket authorizer
- **Lambda Authorizer**: Secure authentication for WebSocket connections
- **Step Functions**: State machine for causal analysis workflow
- **API Gateway WebSocket**: Secure real-time communication with authentication
- **Cognito User Pool**: User authentication and management
- **DynamoDB**: Session and state storage
- **S3 Buckets**: Data storage and artifacts
- **ECS Cluster**: For heavy computation tasks (EDA and analysis)
- **VPC**: Private networking for ECS tasks
- **IAM Roles**: Least-privilege permissions for all services
- **Secrets Manager**: Secure storage for OpenAI API key and JWT secrets

## Testing the Deployment

### 1. Verify Infrastructure

```bash
# Check if all Lambda functions are deployed
aws lambda list-functions --query 'Functions[?contains(FunctionName, `causal-analysis-dev`)].FunctionName'

# Check Step Functions state machine
aws stepfunctions list-state-machines --query 'stateMachines[?contains(name, `causal-analysis-dev`)].name'
```

### 2. Test WebSocket Connection

Use the frontend application or a WebSocket client to connect to the API Gateway WebSocket endpoint.

### 3. Run a Sample Query

Send a causal analysis query through the WebSocket connection:
```json
{
  "query": {
    "query_type": "effect_estimation",
    "treatment_variable": "discounts",
    "outcome_variable": "purchase_amount",
    "confounders": ["customer_age", "customer_income", "seasonality", "ad_exposure"]
  },
  "dag_file": "causal_analysis/config/ecommerce_dag.json",
  "data_file": "sample_data/eCommerce_sales.csv"
}
```

## Monitoring and Debugging

### CloudWatch Logs

Monitor Lambda function logs:
```bash
# View logs for a specific function
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/causal-analysis-dev

# Follow logs in real-time
aws logs tail /aws/lambda/causal-analysis-dev-parse-initial-query --follow
```

### Step Functions Execution

Monitor workflow executions:
```bash
aws stepfunctions list-executions --state-machine-arn "arn:aws:states:me-south-1:ACCOUNT:stateMachine:causal-analysis-dev-agent-sm"
```

## Cleanup

To destroy the infrastructure and avoid charges:

```bash
cd terraform
terraform destroy

# Delete the Terraform state bucket (optional)
aws s3 rm "s3://$BUCKET_NAME" --recursive
aws s3 rb "s3://$BUCKET_NAME"
```

## Troubleshooting

### Common Issues

1. **Lambda packaging errors**
   - Ensure Python dependencies are compatible with Lambda runtime
   - Check file paths in the packaging script

2. **Terraform state issues**
   - Ensure S3 bucket exists and is accessible
   - Check AWS credentials and permissions

3. **Step Functions failures**
   - Check Lambda function logs in CloudWatch
   - Verify IAM roles have proper permissions
   - Check input data format

4. **WebSocket connection issues**
   - Verify API Gateway deployment
   - Check CORS configuration
   - Ensure authentication is properly configured

### Getting Help

- Check CloudWatch Logs for detailed error messages
- Review Terraform outputs for resource details
- Use AWS CloudShell for debugging AWS-specific issues

## Security Considerations

- **API Keys**: OpenAI API key is securely stored in AWS Secrets Manager (not in plaintext files)
- **Authentication**: WebSocket API uses AWS Cognito + Lambda authorizer for secure authentication
- **IAM Roles**: All services follow least-privilege principle with minimal required permissions
- **S3 Buckets**: Have proper access policies and are not publicly accessible
- **Secrets Access**: Lambda functions have IAM permissions to access only their required secrets
- **No Hardcoded Secrets**: All sensitive data is stored in AWS Secrets Manager

## Cost Optimization

- Lambda functions use appropriate memory settings
- ECS tasks are configured for FARGATE spot instances where possible
- S3 storage classes are optimized for access patterns
- CloudWatch log retention is set appropriately

---

For additional support, refer to the project documentation or create an issue in the repository.
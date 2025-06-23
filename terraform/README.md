# AWS Causal Analysis Infrastructure

This Terraform configuration provisions a complete AWS infrastructure for a causal analysis application with AI-powered agent capabilities.

## Architecture Overview

The infrastructure includes:

- **WebSocket API Gateway** for real-time client communication
- **Lambda functions** for serverless compute
- **Step Functions** orchestrating REACT loop workflows
- **ECS Fargate** for containerized analysis workloads
- **DynamoDB** for session management
- **S3 buckets** for data storage
- **Cognito** for user authentication
- **Secrets Manager** for API key storage

## Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform >= 1.0 installed
- An existing S3 bucket for Terraform state storage

## Quick Start

1. **Clone and navigate to the project:**
   ```bash
   cd terraform
   ```

2. **Update backend configuration:**
   Edit `main.tf` and replace `terraform-state-bucket` with your actual S3 bucket name:
   ```hcl
   backend "s3" {
     bucket = "your-terraform-state-bucket"
     key    = "terraform.tfstate"
     region = "me-south-1"
   }
   ```

3. **Initialize Terraform:**
   ```bash
   terraform init
   ```

4. **Plan the deployment:**
   ```bash
   terraform plan
   ```

5. **Deploy the infrastructure:**
   ```bash
   terraform apply
   ```

## Configuration

### Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_name` | Name of the project | `"causal-analysis"` |
| `environment` | Environment name | `"dev"` |

### Customization

Create a `terraform.tfvars` file to override defaults:
```hcl
project_name = "my-project"
environment  = "prod"
```

## Post-Deployment Setup

### 1. Update API Key Secret

After deployment, update the API key in Secrets Manager:

```bash
aws secretsmanager update-secret \
  --secret-id causal-analysis-dev-api-key \
  --secret-string '{"api_key":"your-actual-api-key"}' \
  --region me-south-1
```

### 2. Build and Push Docker Images

Build and push your EDA and analysis container images:

```bash
# Get ECR login token
aws ecr get-login-password --region me-south-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.me-south-1.amazonaws.com

# Build and push EDA image
docker build -t causal-analysis-dev-eda ./eda
docker tag causal-analysis-dev-eda:latest <account-id>.dkr.ecr.me-south-1.amazonaws.com/causal-analysis-dev-eda:latest
docker push <account-id>.dkr.ecr.me-south-1.amazonaws.com/causal-analysis-dev-eda:latest

# Build and push analysis image
docker build -t causal-analysis-dev-analysis ./analysis
docker tag causal-analysis-dev-analysis:latest <account-id>.dkr.ecr.me-south-1.amazonaws.com/causal-analysis-dev-analysis:latest
docker push <account-id>.dkr.ecr.me-south-1.amazonaws.com/causal-analysis-dev-analysis:latest
```

### 3. Deploy Lambda Function Code

Package and deploy your Lambda function code:

```bash
# Example for websocket handler
zip -r websocket-handler.zip lambda/websocket_handler/
aws lambda update-function-code \
  --function-name causal-analysis-dev-websocket-handler \
  --zip-file fileb://websocket-handler.zip \
  --region me-south-1
```

### 4. Configure Networking (if using ECS)

Update the Step Functions state machine definition with actual subnet and security group IDs:

1. Create or identify your VPC, subnets, and security groups
2. Update the `modules/stepfunctions/main.tf` file:
   ```hcl
   NetworkConfiguration = {
     AwsvpcConfiguration = {
       Subnets        = ["subnet-actual-id"]
       SecurityGroups = ["sg-actual-id"]
       AssignPublicIp = "ENABLED"
     }
   }
   ```
3. Run `terraform apply` to update the state machine

## Module Structure

```
modules/
├── apigateway/     # WebSocket API Gateway
├── cognito/        # User Pool and Client
├── dynamodb/       # Session storage table
├── ecs/            # Container cluster and task definitions
├── iam/            # Roles and policies
├── lambda/         # Serverless functions
├── s3/             # Storage buckets
├── secrets/        # API key management
└── stepfunctions/  # Workflow orchestration
```

## Outputs

After deployment, key outputs include:

- `websocket_endpoint` - WebSocket API Gateway URL
- `state_machine_arn` - Step Functions state machine ARN
- `dynamodb_table_name` - Session table name
- `cognito_user_pool_id` - User pool identifier
- `rawdata_bucket_name` - Raw data S3 bucket
- `artifacts_bucket_name` - Analysis outputs S3 bucket

## Security Considerations

- All S3 buckets are private with public access blocked
- Server-side encryption enabled on all storage
- IAM roles follow least privilege principle
- Secrets are managed through AWS Secrets Manager
- CloudWatch logging enabled for all services

## Cost Optimization

- DynamoDB uses PAY_PER_REQUEST billing
- ECS tasks run on Fargate (pay-per-use)
- Lambda functions have appropriate timeout and memory settings
- S3 lifecycle rules manage object retention
- CloudWatch log retention set to 7 days

## Monitoring and Logging

- CloudWatch logs for Lambda functions
- ECS container logs in CloudWatch
- Step Functions execution history
- API Gateway access logs (can be enabled)

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Note:** Ensure S3 buckets are empty before destruction, as versioned objects may prevent deletion.

## Troubleshooting

### Common Issues

1. **Terraform state bucket doesn't exist**
   - Create the S3 bucket manually before running `terraform init`

2. **ECR images not found**
   - Push initial container images before running ECS tasks

3. **Lambda function deployment package too large**
   - Use Lambda layers for dependencies
   - Consider containerized Lambda functions

4. **Step Functions execution fails**
   - Check CloudWatch logs for Lambda function errors
   - Verify ECS task networking configuration

### Support

For infrastructure issues:
1. Check AWS CloudWatch logs
2. Review Terraform state and plan output
3. Verify IAM permissions and resource dependencies

## License

This infrastructure code is provided as-is for educational and development purposes.
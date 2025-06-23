#!/bin/bash
set -e

echo "Deploying Lambda functions..."

LAMBDA_DIR="./local-cloud/lambdas"

# Function to create a Lambda function
create_lambda() {
    local function_name=$1
    local handler=$2
    local runtime=${3:-python3.9}
    local timeout=${4:-60}
    local memory=${5:-256}
    
    echo "Creating Lambda function: $function_name"
    
    # Create deployment package
    (cd "$LAMBDA_DIR/$function_name" && zip -r /tmp/$function_name.zip .)
    
    # Create the Lambda function (ignore if exists)
    gtimeout 30s awslocal --region eu-central-1 lambda create-function \
        --function-name causal-analysis-dev-$function_name \
        --runtime $runtime \
        --role arn:aws:iam::000000000000:role/lambda-execution-role \
        --handler $handler \
        --zip-file fileb:///tmp/$function_name.zip \
        --timeout $timeout \
        --memory-size $memory \
        --environment "Variables={DYNAMODB_ENDPOINT=http://localstack:4566,S3_ENDPOINT=http://localstack:4566,SECRETS_ENDPOINT=http://localstack:4566,STEP_FUNCTIONS_ENDPOINT=http://localstack:4566,ENVIRONMENT=dev}" \
        --tags Project=causal-analysis,Environment=dev 2>/dev/null || echo "Function causal-analysis-dev-$function_name already exists, skipping..."
    
    # Clean up
    rm /tmp/$function_name.zip
}

# Create IAM role for Lambda execution (LocalStack doesn't enforce IAM)
awslocal --region eu-central-1 iam create-role \
    --role-name lambda-execution-role \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    }' 2>/dev/null || true

# Deploy all Lambda functions
create_lambda "websocket-handler" "index.handler" "python3.9" 30 512
create_lambda "parse-initial-query" "index.handler" "python3.9" 30 256
create_lambda "invoke-llm" "index.handler" "python3.9" 120 512
create_lambda "dispatch-tool" "index.handler" "python3.9" 30 256
create_lambda "data-query" "index.handler" "python3.9" 30 256
create_lambda "send-prompt" "index.handler" "python3.9" 30 256
create_lambda "append-tool-output" "index.handler" "python3.9" 30 256
create_lambda "handle-finish" "index.handler" "python3.9" 30 256
create_lambda "handle-error" "index.handler" "python3.9" 30 256
create_lambda "handle-timeout" "index.handler" "python3.9" 30 256

# Create Lambda aliases for versioning
for function in websocket-handler parse-initial-query invoke-llm dispatch-tool data-query send-prompt append-tool-output handle-finish handle-error handle-timeout; do
    awslocal --region eu-central-1 lambda create-alias \
        --function-name causal-analysis-dev-$function \
        --name live \
        --function-version \$LATEST \
        --description "Live alias for $function"
done

# Grant API Gateway permission to invoke WebSocket handler
awslocal --region eu-central-1 lambda add-permission \
    --function-name causal-analysis-dev-websocket-handler \
    --statement-id apigateway-websocket \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com

echo "Lambda functions deployed successfully!"

# List all functions
echo "Deployed functions:"
awslocal --region eu-central-1 lambda list-functions --query 'Functions[*].FunctionName' --output table
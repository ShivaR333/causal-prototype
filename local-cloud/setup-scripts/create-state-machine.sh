#!/bin/bash
set -e

echo "Creating Step Functions state machine..."

# Create IAM role for Step Functions (LocalStack doesn't enforce IAM)
awslocal iam create-role \
    --role-name stepfunctions-execution-role \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": "states.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    }' 2>/dev/null || true

# Read state machine definition
STATE_MACHINE_DEF=$(cat ./local-cloud/step-functions/agent-workflow.json)

# Create state machine
STATE_MACHINE_ARN=$(gtimeout 30s awslocal stepfunctions create-state-machine \
    --name causal-analysis-dev-agent-sm \
    --definition "$STATE_MACHINE_DEF" \
    --role-arn arn:aws:iam::000000000000:role/stepfunctions-execution-role \
    --type STANDARD \
    --logging-configuration '{
        "level": "ALL",
        "includeExecutionData": true,
        "destinations": [{
            "cloudWatchLogsLogGroup": {
                "logGroupArn": "arn:aws:logs:eu-central-1:000000000000:log-group:/aws/stepfunctions/causal-analysis-dev"
            }
        }]
    }' \
    --tags key=Project,value=causal-analysis key=Environment,value=dev \
    --query 'stateMachineArn' \
    --output text)

echo "Created state machine: $STATE_MACHINE_ARN"

# Store ARN in parameter store
awslocal ssm put-parameter \
    --name /causal-analysis/dev/stepfunctions/state-machine-arn \
    --value $STATE_MACHINE_ARN \
    --type String

# Create CloudWatch log group for state machine
awslocal logs create-log-group \
    --log-group-name /aws/stepfunctions/causal-analysis-dev

# Set retention policy
awslocal logs put-retention-policy \
    --log-group-name /aws/stepfunctions/causal-analysis-dev \
    --retention-in-days 7

echo "Step Functions state machine created successfully!"
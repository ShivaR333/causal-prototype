#!/bin/bash
set -e

echo "Creating DynamoDB tables..."

# Create sessions table
gtimeout 30s awslocal dynamodb create-table \
    --table-name causal-analysis-dev-sessions \
    --attribute-definitions \
        AttributeName=sessionId,AttributeType=S \
        AttributeName=userId,AttributeType=S \
        AttributeName=timestamp,AttributeType=N \
    --key-schema \
        AttributeName=sessionId,KeyType=HASH \
    --global-secondary-indexes \
        '[{
            "IndexName": "userId-timestamp-index",
            "KeySchema": [
                {"AttributeName": "userId", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"}
            ],
            "Projection": {"ProjectionType": "ALL"}
        }]' \
    --billing-mode PAY_PER_REQUEST \
    --tags Key=Project,Value=causal-analysis Key=Environment,Value=dev

# Create connections table for WebSocket
gtimeout 30s awslocal dynamodb create-table \
    --table-name causal-analysis-dev-connections \
    --attribute-definitions \
        AttributeName=connectionId,AttributeType=S \
        AttributeName=userId,AttributeType=S \
    --key-schema \
        AttributeName=connectionId,KeyType=HASH \
    --global-secondary-indexes \
        '[{
            "IndexName": "userId-index",
            "KeySchema": [
                {"AttributeName": "userId", "KeyType": "HASH"}
            ],
            "Projection": {"ProjectionType": "ALL"}
        }]' \
    --billing-mode PAY_PER_REQUEST \
    --tags Key=Project,Value=causal-analysis Key=Environment,Value=dev

# Create analysis jobs table
gtimeout 30s awslocal dynamodb create-table \
    --table-name causal-analysis-dev-jobs \
    --attribute-definitions \
        AttributeName=jobId,AttributeType=S \
        AttributeName=sessionId,AttributeType=S \
        AttributeName=status,AttributeType=S \
        AttributeName=createdAt,AttributeType=N \
    --key-schema \
        AttributeName=jobId,KeyType=HASH \
    --global-secondary-indexes \
        '[{
            "IndexName": "sessionId-createdAt-index",
            "KeySchema": [
                {"AttributeName": "sessionId", "KeyType": "HASH"},
                {"AttributeName": "createdAt", "KeyType": "RANGE"}
            ],
            "Projection": {"ProjectionType": "ALL"}
        },
        {
            "IndexName": "status-createdAt-index",
            "KeySchema": [
                {"AttributeName": "status", "KeyType": "HASH"},
                {"AttributeName": "createdAt", "KeyType": "RANGE"}
            ],
            "Projection": {"ProjectionType": "ALL"}
        }]' \
    --billing-mode PAY_PER_REQUEST \
    --tags Key=Project,Value=causal-analysis Key=Environment,Value=dev

# Enable point-in-time recovery for sessions table
gtimeout 30s awslocal dynamodb update-continuous-backups \
    --table-name causal-analysis-dev-sessions \
    --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true

# Set up TTL for connections table (24 hours)
gtimeout 30s awslocal dynamodb update-time-to-live \
    --table-name causal-analysis-dev-connections \
    --time-to-live-specification Enabled=true,AttributeName=ttl

# Set up TTL for jobs table (7 days)
gtimeout 30s awslocal dynamodb update-time-to-live \
    --table-name causal-analysis-dev-jobs \
    --time-to-live-specification Enabled=true,AttributeName=ttl

echo "DynamoDB tables created successfully!"
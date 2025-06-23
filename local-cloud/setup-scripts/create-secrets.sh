#!/bin/bash
set -e

echo "Creating secrets in Secrets Manager..."

# Create API key secret
awslocal secretsmanager create-secret \
    --name causal-analysis-dev-api-key \
    --description "API key for LLM services" \
    --secret-string '{
        "openai_api_key": "test-openai-key-for-local-dev",
        "anthropic_api_key": "test-anthropic-key-for-local-dev"
    }' \
    --tags Key=Project,Value=causal-analysis Key=Environment,Value=dev

# Create database credentials (for future use)
awslocal secretsmanager create-secret \
    --name causal-analysis-dev-db-credentials \
    --description "Database credentials" \
    --secret-string '{
        "username": "admin",
        "password": "local-test-password",
        "host": "localhost",
        "port": 5432,
        "database": "causal_analysis"
    }' \
    --tags Key=Project,Value=causal-analysis Key=Environment,Value=dev

# Create JWT secret for token signing
awslocal secretsmanager create-secret \
    --name causal-analysis-dev-jwt-secret \
    --description "JWT signing secret" \
    --secret-string '{
        "secret": "local-jwt-secret-key-for-development-only",
        "algorithm": "HS256",
        "expiration_hours": 24
    }' \
    --tags Key=Project,Value=causal-analysis Key=Environment,Value=dev

# Create webhook secret (for future integrations)
awslocal secretsmanager create-secret \
    --name causal-analysis-dev-webhook-secret \
    --description "Webhook signing secret" \
    --secret-string '{
        "secret": "webhook-secret-for-local-testing"
    }' \
    --tags Key=Project,Value=causal-analysis Key=Environment,Value=dev

echo "Secrets created successfully!"

# List all secrets
echo "Created secrets:"
awslocal secretsmanager list-secrets --query 'SecretList[*].Name' --output table
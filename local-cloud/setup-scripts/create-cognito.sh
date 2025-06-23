#!/bin/bash
set -e

echo "Creating Cognito resources..."

# Create user pool
USER_POOL_ID=$(awslocal cognito-idp create-user-pool \
    --pool-name causal-analysis-dev-user-pool \
    --policies '{
        "PasswordPolicy": {
            "MinimumLength": 8,
            "RequireUppercase": true,
            "RequireLowercase": true,
            "RequireNumbers": true,
            "RequireSymbols": false
        }
    }' \
    --auto-verified-attributes email \
    --username-attributes email \
    --mfa-configuration OFF \
    --account-recovery-setting '{
        "RecoveryMechanisms": [{
            "Priority": 1,
            "Name": "verified_email"
        }]
    }' \
    --query 'UserPool.Id' \
    --output text)

echo "Created User Pool: $USER_POOL_ID"

# Create user pool client
CLIENT_ID=$(awslocal cognito-idp create-user-pool-client \
    --user-pool-id $USER_POOL_ID \
    --client-name causal-analysis-dev-web-client \
    --generate-secret \
    --explicit-auth-flows \
        ALLOW_USER_PASSWORD_AUTH \
        ALLOW_REFRESH_TOKEN_AUTH \
        ALLOW_USER_SRP_AUTH \
    --prevent-user-existence-errors ENABLED \
    --enable-token-revocation \
    --access-token-validity 1 \
    --id-token-validity 1 \
    --refresh-token-validity 30 \
    --token-validity-units '{
        "AccessToken": "hours",
        "IdToken": "hours",
        "RefreshToken": "days"
    }' \
    --query 'UserPoolClient.ClientId' \
    --output text)

echo "Created User Pool Client: $CLIENT_ID"

# Create user pool domain
awslocal cognito-idp create-user-pool-domain \
    --domain causal-analysis-dev-auth \
    --user-pool-id $USER_POOL_ID

# Create test users for development
echo "Creating test users..."

# Admin user
awslocal cognito-idp admin-create-user \
    --user-pool-id $USER_POOL_ID \
    --username admin@example.com \
    --user-attributes \
        Name=email,Value=admin@example.com \
        Name=email_verified,Value=true \
    --temporary-password TempPass123! \
    --message-action SUPPRESS

# Set permanent password for admin
awslocal cognito-idp admin-set-user-password \
    --user-pool-id $USER_POOL_ID \
    --username admin@example.com \
    --password AdminPass123! \
    --permanent

# Regular test user
awslocal cognito-idp admin-create-user \
    --user-pool-id $USER_POOL_ID \
    --username user@example.com \
    --user-attributes \
        Name=email,Value=user@example.com \
        Name=email_verified,Value=true \
    --temporary-password TempPass123! \
    --message-action SUPPRESS

# Set permanent password for user
awslocal cognito-idp admin-set-user-password \
    --user-pool-id $USER_POOL_ID \
    --username user@example.com \
    --password UserPass123! \
    --permanent

# Save configuration for application use
cat > /tmp/cognito-config.json <<EOF
{
    "userPoolId": "$USER_POOL_ID",
    "clientId": "$CLIENT_ID",
    "region": "us-east-1",
    "endpoint": "http://localhost:4566",
    "testUsers": [
        {
            "email": "admin@example.com",
            "password": "AdminPass123!"
        },
        {
            "email": "user@example.com",
            "password": "UserPass123!"
        }
    ]
}
EOF

echo "Cognito configuration saved to /tmp/cognito-config.json"

# Store in parameter store for easy access
awslocal ssm put-parameter \
    --name /causal-analysis/dev/cognito/user-pool-id \
    --value $USER_POOL_ID \
    --type String

awslocal ssm put-parameter \
    --name /causal-analysis/dev/cognito/client-id \
    --value $CLIENT_ID \
    --type String

echo "Cognito resources created successfully!"
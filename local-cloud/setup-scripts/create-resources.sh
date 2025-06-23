#!/bin/bash
# set -e

echo "Setting up LocalStack resources..."

# Wait for LocalStack to be ready
echo "Waiting for LocalStack to be ready..."
until awslocal s3 ls > /dev/null 2>&1; do
    echo "Waiting for LocalStack..."
    sleep 2
done

echo "LocalStack is ready. Creating resources..."

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Run individual setup scripts
"$SCRIPT_DIR/create-buckets.sh"
"$SCRIPT_DIR/create-tables.sh"
"$SCRIPT_DIR/create-secrets.sh"
# "$SCRIPT_DIR/create-cognito.sh"
"$SCRIPT_DIR/deploy-lambdas.sh"
"$SCRIPT_DIR/create-state-machine.sh"

echo "All resources created successfully!"
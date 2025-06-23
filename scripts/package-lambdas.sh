#!/bin/bash

# Lambda packaging script for AWS deployment
# This script packages all Lambda functions with their dependencies

set -e

PROJECT_ROOT=$(pwd)
LAMBDA_DIR="local-cloud/lambdas"
PACKAGE_DIR="lambda-packages"

echo "🚀 Starting Lambda packaging process..."

# Create package directory
mkdir -p $PACKAGE_DIR

# Function to package a single Lambda
package_lambda() {
    local lambda_name=$1
    local lambda_path="$LAMBDA_DIR/$lambda_name"
    local package_path="$PACKAGE_DIR/${lambda_name}.zip"
    
    echo "📦 Packaging $lambda_name..."
    
    if [ ! -d "$lambda_path" ]; then
        echo "❌ Lambda directory not found: $lambda_path"
        return 1
    fi
    
    # Create temporary directory
    temp_dir=$(mktemp -d)
    
    # Copy Lambda code
    cp "$lambda_path/index.py" "$temp_dir/"
    
    # Install dependencies if requirements.txt exists
    if [ -f "$lambda_path/requirements.txt" ]; then
        echo "  📋 Installing dependencies for $lambda_name..."
        pip install -r "$lambda_path/requirements.txt" -t "$temp_dir/" --quiet
    fi
    
    # Create ZIP package
    cd "$temp_dir"
    zip -r "$PROJECT_ROOT/$package_path" . > /dev/null
    cd "$PROJECT_ROOT"
    
    # Cleanup
    rm -rf "$temp_dir"
    
    echo "  ✅ Packaged: $package_path"
}

# List of Lambda functions to package
LAMBDA_FUNCTIONS=(
    "websocket-handler"
    "websocket-authorizer"
    "parse-initial-query"
    "send-prompt"
    "invoke-llm"
    "dispatch-tool"
    "append-tool-output"
    "handle-finish"
    "handle-error"
    "handle-timeout"
    "data-query"
)

# Package each Lambda function
for lambda_func in "${LAMBDA_FUNCTIONS[@]}"; do
    package_lambda "$lambda_func"
done

echo "🎉 All Lambda functions packaged successfully!"
echo "📁 Packages available in: $PACKAGE_DIR/"
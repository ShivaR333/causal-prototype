#!/bin/bash

# AWS Deployment Script for Causal Analysis Platform
# This script automates the complete deployment process

set -e

PROJECT_ROOT=$(pwd)
TERRAFORM_DIR="terraform"
SCRIPTS_DIR="scripts"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}🚀 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check if AWS CLI is installed and configured
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install it first."
        exit 1
    fi
    
    # Check if pip is installed
    if ! command -v pip &> /dev/null; then
        print_error "pip is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_success "All prerequisites met!"
}

# Check Terraform configuration
check_terraform_config() {
    print_step "Checking Terraform configuration..."
    
    cd "$PROJECT_ROOT/$TERRAFORM_DIR"
    
    # Check if terraform.tfvars exists
    if [ ! -f "terraform.tfvars" ]; then
        print_warning "terraform.tfvars file not found!"
        print_warning "Please copy terraform.tfvars.example to terraform.tfvars and fill in your values:"
        print_warning "  cd terraform"
        print_warning "  cp terraform.tfvars.example terraform.tfvars"
        print_warning "  # Edit terraform.tfvars and add your OpenAI API key"
        exit 1
    fi
    
    # Check if OpenAI API key is set
    if grep -q "sk-your-actual-openai-api-key-here" terraform.tfvars; then
        print_error "Please update terraform.tfvars with your actual OpenAI API key!"
        print_error "The placeholder value is still present."
        exit 1
    fi
    
    print_success "Terraform configuration looks good!"
    cd "$PROJECT_ROOT"
}

# Package Lambda functions
package_lambdas() {
    print_step "Packaging Lambda functions..."
    
    cd "$PROJECT_ROOT"
    
    if [ -f "$SCRIPTS_DIR/package-lambdas.sh" ]; then
        bash "$SCRIPTS_DIR/package-lambdas.sh"
        print_success "Lambda functions packaged successfully!"
    else
        print_error "Lambda packaging script not found!"
        exit 1
    fi
}

# Build and push container images
build_containers() {
    print_step "Building and pushing container images to ECR..."
    
    cd "$PROJECT_ROOT"
    
    if [ -f "$SCRIPTS_DIR/build-and-push-containers.sh" ]; then
        # Make sure the script is executable
        chmod +x "$SCRIPTS_DIR/build-and-push-containers.sh"
        
        # Run the container build script
        bash "$SCRIPTS_DIR/build-and-push-containers.sh" --region "$REGION"
        print_success "Container images built and pushed successfully!"
    else
        print_error "Container build script not found!"
        exit 1
    fi
}

# Create S3 bucket for Terraform state (if it doesn't exist)
setup_terraform_backend() {
    print_step "Setting up Terraform backend..."
    
    BUCKET_NAME="terraform-state-bucket-$(date +%s)"
    REGION="${AWS_REGION:-me-south-1}"
    
    # Check if bucket exists
    if aws s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
        print_step "Creating S3 bucket for Terraform state..."
        aws s3 mb "s3://$BUCKET_NAME" --region "$REGION"
        
        # Enable versioning
        aws s3api put-bucket-versioning \
            --bucket "$BUCKET_NAME" \
            --versioning-configuration Status=Enabled
        
        print_success "Terraform state bucket created: $BUCKET_NAME"
        
        # Update terraform configuration with new bucket name
        sed -i.bak "s/terraform-state-bucket/$BUCKET_NAME/g" "$TERRAFORM_DIR/main.tf"
        print_warning "Updated Terraform configuration with bucket name: $BUCKET_NAME"
    else
        print_success "Terraform state bucket already exists or accessible"
    fi
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    print_step "Deploying infrastructure with Terraform..."
    
    cd "$PROJECT_ROOT/$TERRAFORM_DIR"
    
    # Initialize Terraform
    print_step "Initializing Terraform..."
    terraform init
    
    # Plan the deployment
    print_step "Planning Terraform deployment..."
    terraform plan -out=tfplan
    
    # Apply the deployment
    print_step "Applying Terraform deployment..."
    terraform apply tfplan
    
    print_success "Infrastructure deployed successfully!"
    
    # Save outputs
    terraform output > ../terraform-outputs.txt
    print_success "Terraform outputs saved to terraform-outputs.txt"
    
    cd "$PROJECT_ROOT"
}

# Upload sample data to S3
upload_sample_data() {
    print_step "Uploading sample data to S3..."
    
    # Get S3 bucket name from Terraform outputs
    RAWDATA_BUCKET=$(grep -o '"[^"]*"' terraform-outputs.txt | head -1 | tr -d '"')
    
    if [ -z "$RAWDATA_BUCKET" ]; then
        print_warning "Could not determine S3 bucket name from Terraform outputs"
        return
    fi
    
    # Upload sample data
    if [ -d "data/sample_data" ]; then
        aws s3 sync data/sample_data/ "s3://$RAWDATA_BUCKET/sample_data/"
        print_success "Sample data uploaded to S3"
    fi
    
    # Upload DAG configurations
    if [ -d "backend/causal_analysis/config" ]; then
        aws s3 sync backend/causal_analysis/config/ "s3://$RAWDATA_BUCKET/config/"
        print_success "DAG configurations uploaded to S3"
    fi
}

# Test the deployment
test_deployment() {
    print_step "Testing deployment..."
    
    # Get API Gateway endpoint from Terraform outputs
    API_ENDPOINT=$(grep "api_gateway_websocket_url" terraform-outputs.txt | grep -o '"[^"]*"' | tr -d '"')
    
    if [ -n "$API_ENDPOINT" ]; then
        print_success "WebSocket API endpoint: $API_ENDPOINT"
        
        # Test basic connectivity (optional)
        if command -v curl &> /dev/null; then
            print_step "Testing API connectivity..."
            # Add basic API test here if needed
        fi
    else
        print_warning "Could not determine API endpoint from Terraform outputs"
    fi
}

# Main deployment function
main() {
    echo "========================================"
    echo "🚀 AWS Deployment for Causal Analysis Platform"
    echo "========================================"
    
    check_prerequisites
    check_terraform_config
    package_lambdas
    build_containers
    setup_terraform_backend
    deploy_infrastructure
    upload_sample_data
    test_deployment
    
    echo "========================================"
    print_success "Deployment completed successfully!"
    echo "========================================"
    
    print_step "Next steps:"
    echo "1. Check terraform-outputs.txt for resource details"
    echo "2. Update your frontend configuration with the new API endpoint"
    echo "3. Test the WebSocket connection from your frontend"
    echo "4. Monitor CloudWatch logs for any issues"
    
    if [ -f "terraform-outputs.txt" ]; then
        echo ""
        echo "Key outputs:"
        cat terraform-outputs.txt
    fi
}

# Run main function
main "$@"
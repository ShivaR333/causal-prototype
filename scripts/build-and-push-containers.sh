#!/bin/bash

# Container Build and Push Script for ECS/Fargate Deployment
# This script builds Docker images and pushes them to ECR

set -e

PROJECT_ROOT=$(pwd)
BACKEND_DIR="backend"
AWS_REGION="${AWS_REGION:-me-south-1}"
AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID}"
PROJECT_NAME="${PROJECT_NAME:-causal-analysis}"
ENVIRONMENT="${ENVIRONMENT:-dev}"

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
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if AWS CLI is installed and configured
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    # Get AWS Account ID if not provided
    if [ -z "$AWS_ACCOUNT_ID" ]; then
        AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        print_step "Detected AWS Account ID: $AWS_ACCOUNT_ID"
    fi
    
    print_success "All prerequisites met!"
}

# Create ECR repositories if they don't exist
create_ecr_repositories() {
    print_step "Creating ECR repositories if they don't exist..."
    
    local repos=("${PROJECT_NAME}-${ENVIRONMENT}-eda" "${PROJECT_NAME}-${ENVIRONMENT}-analysis")
    
    for repo in "${repos[@]}"; do
        if aws ecr describe-repositories --repository-names "$repo" --region "$AWS_REGION" &> /dev/null; then
            print_success "ECR repository already exists: $repo"
        else
            print_step "Creating ECR repository: $repo"
            aws ecr create-repository \
                --repository-name "$repo" \
                --region "$AWS_REGION" \
                --image-scanning-configuration scanOnPush=true \
                --encryption-configuration encryptionType=AES256
            print_success "Created ECR repository: $repo"
        fi
    done
}

# Login to ECR
ecr_login() {
    print_step "Logging in to ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin \
        "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    print_success "Successfully logged in to ECR"
}

# Build and push EDA container
build_and_push_eda() {
    print_step "Building EDA container..."
    
    local image_name="${PROJECT_NAME}-${ENVIRONMENT}-eda"
    local ecr_uri="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${image_name}"
    
    cd "$PROJECT_ROOT/$BACKEND_DIR"
    
    # Build the Docker image
    docker build -f Dockerfile.eda -t "$image_name:latest" .
    
    # Tag for ECR
    docker tag "$image_name:latest" "$ecr_uri:latest"
    docker tag "$image_name:latest" "$ecr_uri:$(date +%Y%m%d-%H%M%S)"
    
    # Push to ECR
    print_step "Pushing EDA container to ECR..."
    docker push "$ecr_uri:latest"
    docker push "$ecr_uri:$(date +%Y%m%d-%H%M%S)"
    
    print_success "EDA container built and pushed successfully!"
    echo "ECR URI: $ecr_uri:latest"
    
    cd "$PROJECT_ROOT"
}

# Build and push Analysis container
build_and_push_analysis() {
    print_step "Building Analysis container..."
    
    local image_name="${PROJECT_NAME}-${ENVIRONMENT}-analysis"
    local ecr_uri="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${image_name}"
    
    cd "$PROJECT_ROOT/$BACKEND_DIR"
    
    # Build the Docker image
    docker build -f Dockerfile.analysis -t "$image_name:latest" .
    
    # Tag for ECR
    docker tag "$image_name:latest" "$ecr_uri:latest"
    docker tag "$image_name:latest" "$ecr_uri:$(date +%Y%m%d-%H%M%S)"
    
    # Push to ECR
    print_step "Pushing Analysis container to ECR..."
    docker push "$ecr_uri:latest"
    docker push "$ecr_uri:$(date +%Y%m%d-%H%M%S)"
    
    print_success "Analysis container built and pushed successfully!"
    echo "ECR URI: $ecr_uri:latest"
    
    cd "$PROJECT_ROOT"
}

# Clean up local Docker images (optional)
cleanup_local_images() {
    print_step "Cleaning up local Docker images..."
    
    local images=(
        "${PROJECT_NAME}-${ENVIRONMENT}-eda:latest"
        "${PROJECT_NAME}-${ENVIRONMENT}-analysis:latest"
    )
    
    for image in "${images[@]}"; do
        if docker images "$image" -q | head -1 | grep -q .; then
            docker rmi "$image" || true
        fi
    done
    
    print_success "Local images cleaned up"
}

# Display summary
display_summary() {
    echo "========================================"
    print_success "Container build and push completed!"
    echo "========================================"
    
    echo ""
    echo "ECS Container Images:"
    echo "📦 EDA Service: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-${ENVIRONMENT}-eda:latest"
    echo "📦 Analysis Service: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${PROJECT_NAME}-${ENVIRONMENT}-analysis:latest"
    echo ""
    echo "Next steps:"
    echo "1. Deploy infrastructure with Terraform"
    echo "2. ECS tasks will automatically pull these images"
    echo "3. Test the services through Step Functions workflow"
}

# Main function
main() {
    echo "========================================"
    echo "🐳 Container Build and Push for ECS/Fargate"
    echo "========================================"
    
    check_prerequisites
    create_ecr_repositories
    ecr_login
    build_and_push_eda
    build_and_push_analysis
    
    # Ask user if they want to clean up local images
    read -p "Clean up local Docker images? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup_local_images
    fi
    
    display_summary
}

# Handle command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --aws-account-id)
            AWS_ACCOUNT_ID="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --project-name)
            PROJECT_NAME="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --aws-account-id ID    AWS Account ID (auto-detected if not provided)"
            echo "  --region REGION        AWS Region (default: me-south-1)"
            echo "  --project-name NAME    Project name (default: causal-analysis)"
            echo "  --environment ENV      Environment (default: dev)"
            echo "  --help                 Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main "$@"
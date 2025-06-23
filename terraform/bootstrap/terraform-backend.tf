# Bootstrap configuration for Terraform backend
# This must be applied BEFORE the main Terraform configuration
# to create the S3 bucket and DynamoDB table for state management

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  # No backend configuration - uses local state for bootstrap
}

provider "aws" {
  region = var.aws_region
}

# S3 bucket for Terraform state storage
resource "aws_s3_bucket" "terraform_state" {
  bucket = var.terraform_state_bucket

  tags = {
    Name        = var.terraform_state_bucket
    Purpose     = "Terraform state storage"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_s3_bucket_versioning" "terraform_state_versioning" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state_encryption" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state_pab" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# DynamoDB table for Terraform state locking
resource "aws_dynamodb_table" "terraform_state_lock" {
  name           = var.terraform_lock_table
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = var.terraform_lock_table
    Purpose     = "Terraform state locking"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Outputs for reference
output "terraform_state_bucket" {
  description = "Name of the Terraform state S3 bucket"
  value       = aws_s3_bucket.terraform_state.id
}

output "terraform_lock_table" {
  description = "Name of the Terraform state lock DynamoDB table"
  value       = aws_dynamodb_table.terraform_state_lock.name
}

output "next_steps" {
  description = "Instructions for next steps"
  value = "Bootstrap complete. Update main.tf backend configuration with bucket: ${aws_s3_bucket.terraform_state.id} and dynamodb_table: ${aws_dynamodb_table.terraform_state_lock.name}"
}
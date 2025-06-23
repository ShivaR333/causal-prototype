# Terraform Backend Bootstrap

This directory contains the bootstrap configuration that must be applied **before** the main Terraform configuration to set up the S3 bucket and DynamoDB table for remote state management.

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform installed

## Bootstrap Steps

1. **Customize configuration**:
   ```bash
   cd bootstrap
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with unique bucket names for your account
   ```

2. **Apply bootstrap configuration**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

3. **Update main configuration**:
   After bootstrap completes, update the backend configuration in `../main.tf` with the bucket and table names shown in the terraform output.

4. **Initialize main configuration**:
   ```bash
   cd ..
   terraform init  # This will migrate to remote backend
   ```

## Important Notes

- The S3 bucket name must be globally unique across all AWS accounts
- The bootstrap configuration uses local state and should be kept secure
- Only run this once per environment
- Keep the `terraform.tfstate` file from the bootstrap in a secure location
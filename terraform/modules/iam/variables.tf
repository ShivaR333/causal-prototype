variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "secrets_access_policy_arn" {
  description = "ARN of the secrets access policy for Lambda functions"
  type        = string
}

variable "ecs_secrets_access_policy_arn" {
  description = "ARN of the secrets access policy for ECS tasks"
  type        = string
}

# Resource-specific ARNs for least-privilege IAM policies
variable "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  type        = string
}

variable "rawdata_bucket_arn" {
  description = "ARN of the raw data S3 bucket"
  type        = string
}

variable "artifacts_bucket_arn" {
  description = "ARN of the artifacts S3 bucket"
  type        = string
}


variable "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  type        = string
}

variable "eda_task_definition_arn" {
  description = "ARN of the EDA task definition"
  type        = string
}

variable "analysis_task_definition_arn" {
  description = "ARN of the analysis task definition"
  type        = string
}

variable "api_gateway_execution_arn" {
  description = "ARN for API Gateway execution access (manage connections)"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID for scoping IAM permissions"
  type        = string
}
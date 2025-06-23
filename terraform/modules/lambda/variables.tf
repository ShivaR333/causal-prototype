variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "lambda_execution_role" {
  description = "ARN of the Lambda execution role"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "rawdata_bucket_name" {
  description = "Name of the raw data S3 bucket"
  type        = string
}

variable "artifacts_bucket_name" {
  description = "Name of the artifacts S3 bucket"
  type        = string
}

variable "openai_secret_arn" {
  description = "ARN of the OpenAI API key secret"
  type        = string
}

variable "jwt_secret_arn" {
  description = "ARN of the JWT secret"
  type        = string
}

variable "step_function_arn" {
  description = "ARN of the Step Functions state machine"
  type        = string
}

variable "user_pool_id" {
  description = "Cognito User Pool ID"
  type        = string
}

variable "user_pool_client_id" {
  description = "Cognito User Pool Client ID"
  type        = string
}
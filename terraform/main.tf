terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "terraform-state-bucket"
    key            = "terraform.tfstate"
    region         = "me-south-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}

# Get current AWS account information
data "aws_caller_identity" "current" {}

# Note: The DynamoDB table for Terraform state locking must be created separately
# before running this configuration. See bootstrap/terraform-backend.tf

module "vpc" {
  source = "./modules/vpc"
  
  project_name = var.project_name
  environment  = var.environment
}

module "iam" {
  source = "./modules/iam"
  
  project_name                    = var.project_name
  environment                     = var.environment
  secrets_access_policy_arn       = module.secrets.secrets_access_policy_arn
  ecs_secrets_access_policy_arn   = module.secrets.ecs_secrets_access_policy_arn
  
  # Resource-specific ARNs for least-privilege policies
  dynamodb_table_arn              = module.dynamodb.table_arn
  rawdata_bucket_arn              = module.s3.rawdata_bucket_arn
  artifacts_bucket_arn            = module.s3.artifacts_bucket_arn
  ecs_cluster_arn                 = module.ecs.cluster_arn
  eda_task_definition_arn         = module.ecs.eda_task_definition_arn
  analysis_task_definition_arn    = module.ecs.analysis_task_definition_arn
  api_gateway_execution_arn       = module.apigateway.websocket_execution_arn
  aws_account_id                  = data.aws_caller_identity.current.account_id
}

module "dynamodb" {
  source = "./modules/dynamodb"
  
  project_name = var.project_name
  environment  = var.environment
}

module "s3" {
  source = "./modules/s3"
  
  project_name   = var.project_name
  environment    = var.environment
  aws_account_id = data.aws_caller_identity.current.account_id
}

module "cognito" {
  source = "./modules/cognito"
  
  project_name  = var.project_name
  environment   = var.environment
  callback_urls = var.callback_urls
  logout_urls   = var.logout_urls
}

module "secrets" {
  source = "./modules/secrets"
  
  project_name    = var.project_name
  environment     = var.environment
  openai_api_key  = var.openai_api_key
  openai_model    = var.openai_model
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

module "lambda" {
  source = "./modules/lambda"
  
  project_name          = var.project_name
  environment           = var.environment
  lambda_execution_role = module.iam.lambda_execution_role_arn
  dynamodb_table_name   = module.dynamodb.table_name
  rawdata_bucket_name   = module.s3.rawdata_bucket_name
  artifacts_bucket_name = module.s3.artifacts_bucket_name
  openai_secret_arn    = module.secrets.openai_api_key_secret_arn
  jwt_secret_arn       = module.secrets.jwt_secret_arn
  step_function_arn    = module.stepfunctions.state_machine_arn
  user_pool_id         = module.cognito.user_pool_id
  user_pool_client_id  = module.cognito.user_pool_client_id
}

module "apigateway" {
  source = "./modules/apigateway"
  
  project_name                = var.project_name
  environment                 = var.environment
  websocket_handler_invoke_arn = module.lambda.websocket_handler_invoke_arn
  websocket_handler_arn       = module.lambda.websocket_handler_arn
  websocket_authorizer_arn    = module.lambda.websocket_authorizer_arn
  websocket_authorizer_invoke_arn = module.lambda.websocket_authorizer_invoke_arn
}

module "stepfunctions" {
  source = "./modules/stepfunctions"
  
  project_name              = var.project_name
  environment               = var.environment
  step_functions_role_arn   = module.iam.step_functions_execution_role_arn
  parse_query_lambda_arn    = module.lambda.parse_initial_query_arn
  send_prompt_lambda_arn    = module.lambda.send_prompt_arn
  invoke_llm_lambda_arn     = module.lambda.invoke_llm_arn
  dispatch_tool_lambda_arn  = module.lambda.dispatch_tool_arn
  append_output_lambda_arn  = module.lambda.append_tool_output_arn
  handle_finish_lambda_arn  = module.lambda.handle_finish_arn
  data_query_lambda_arn     = module.lambda.data_query_arn
  handle_error_lambda_arn   = module.lambda.handle_error_arn
  handle_timeout_lambda_arn = module.lambda.handle_timeout_arn
  ecs_cluster_arn          = module.ecs.cluster_arn
  eda_task_definition_arn  = module.ecs.eda_task_definition_arn
  analysis_task_definition_arn = module.ecs.analysis_task_definition_arn
  
  # VPC configuration for ECS tasks
  private_subnet_ids       = module.vpc.private_subnet_ids
  ecs_security_group_id    = module.vpc.ecs_tasks_security_group_id
}

module "ecs" {
  source = "./modules/ecs"
  
  project_name           = var.project_name
  environment            = var.environment
  ecs_task_execution_role = module.iam.ecs_task_execution_role_arn
  ecs_task_role          = module.iam.ecs_task_role_arn
  vpc_id                 = module.vpc.vpc_id
  private_subnet_ids     = module.vpc.private_subnet_ids
  ecs_security_group_id  = module.vpc.ecs_tasks_security_group_id
  aws_region             = var.aws_region
}
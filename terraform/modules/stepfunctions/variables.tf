variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "step_functions_role_arn" {
  description = "ARN of the Step Functions execution role"
  type        = string
}

variable "parse_query_lambda_arn" {
  description = "ARN of the parse initial query Lambda function"
  type        = string
}

variable "send_prompt_lambda_arn" {
  description = "ARN of the send prompt Lambda function"
  type        = string
}

variable "invoke_llm_lambda_arn" {
  description = "ARN of the invoke LLM Lambda function"
  type        = string
}

variable "dispatch_tool_lambda_arn" {
  description = "ARN of the dispatch tool Lambda function"
  type        = string
}

variable "append_output_lambda_arn" {
  description = "ARN of the append tool output Lambda function"
  type        = string
}

variable "handle_finish_lambda_arn" {
  description = "ARN of the handle finish Lambda function"
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

variable "data_query_lambda_arn" {
  description = "ARN of the data query Lambda function"
  type        = string
}

variable "handle_error_lambda_arn" {
  description = "ARN of the handle error Lambda function"
  type        = string
}

variable "handle_timeout_lambda_arn" {
  description = "ARN of the handle timeout Lambda function"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
  type        = string
}
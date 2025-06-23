variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "websocket_handler_invoke_arn" {
  description = "Invoke ARN of the websocket handler Lambda function"
  type        = string
}

variable "websocket_handler_arn" {
  description = "ARN of the websocket handler Lambda function"
  type        = string
}

variable "websocket_authorizer_arn" {
  description = "ARN of the websocket authorizer Lambda function"
  type        = string
}

variable "websocket_authorizer_invoke_arn" {
  description = "Invoke ARN of the websocket authorizer Lambda function"
  type        = string
}
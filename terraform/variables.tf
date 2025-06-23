variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "causal-analysis"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "me-south-1"
}

variable "openai_api_key" {
  description = "OpenAI API key for LLM integration"
  type        = string
  sensitive   = true
}

variable "openai_model" {
  description = "OpenAI model to use"
  type        = string
  default     = "gpt-3.5-turbo"
}

variable "callback_urls" {
  description = "List of allowed callback URLs for Cognito OAuth"
  type        = list(string)
}

variable "logout_urls" {
  description = "List of allowed logout URLs for Cognito OAuth"
  type        = list(string)
}
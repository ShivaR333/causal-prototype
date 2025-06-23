variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "callback_urls" {
  description = "List of allowed callback URLs for OAuth"
  type        = list(string)
}

variable "logout_urls" {
  description = "List of allowed logout URLs for OAuth"
  type        = list(string)
}
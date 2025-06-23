output "openai_api_key_secret_arn" {
  description = "ARN of the OpenAI API key secret"
  value       = aws_secretsmanager_secret.openai_api_key.arn
}

output "openai_api_key_secret_name" {
  description = "Name of the OpenAI API key secret"
  value       = aws_secretsmanager_secret.openai_api_key.name
}

output "jwt_secret_arn" {
  description = "ARN of the JWT secret"
  value       = aws_secretsmanager_secret.jwt_secret.arn
}

output "jwt_secret_name" {
  description = "Name of the JWT secret"
  value       = aws_secretsmanager_secret.jwt_secret.name
}

output "secrets_access_policy_arn" {
  description = "ARN of the secrets access policy for Lambda functions"
  value       = aws_iam_policy.secrets_access.arn
}

output "ecs_secrets_access_policy_arn" {
  description = "ARN of the secrets access policy for ECS tasks"
  value       = aws_iam_policy.ecs_secrets_access.arn
}
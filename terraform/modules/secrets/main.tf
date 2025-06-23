# OpenAI API Key Secret
resource "aws_secretsmanager_secret" "openai_api_key" {
  name                    = "${var.project_name}-${var.environment}-openai-api-key"
  description             = "OpenAI API key for LLM integration in causal analysis platform"
  recovery_window_in_days = 7

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-openai-api-key"
    Type = "api-key"
  })
}

# OpenAI API Key Secret Version
resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id = aws_secretsmanager_secret.openai_api_key.id
  secret_string = jsonencode({
    api_key = var.openai_api_key
    model   = var.openai_model
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# JWT Secret for Lambda authorizer
resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "${var.project_name}-${var.environment}-jwt-secret"
  description             = "JWT secret for WebSocket authentication"
  recovery_window_in_days = 7

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-jwt-secret"
    Type = "jwt-secret"
  })
}

# Generate a random JWT secret
resource "random_password" "jwt_secret" {
  length  = 64
  special = true
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id = aws_secretsmanager_secret.jwt_secret.id
  secret_string = jsonencode({
    secret = random_password.jwt_secret.result
  })
}

# IAM Policy for Lambda functions to access secrets
resource "aws_iam_policy" "secrets_access" {
  name        = "${var.project_name}-${var.environment}-secrets-access"
  description = "Policy for Lambda functions to access Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.openai_api_key.arn,
          aws_secretsmanager_secret.jwt_secret.arn
        ]
      }
    ]
  })

  tags = var.common_tags
}

# IAM Policy for ECS tasks to access secrets
resource "aws_iam_policy" "ecs_secrets_access" {
  name        = "${var.project_name}-${var.environment}-ecs-secrets-access"
  description = "Policy for ECS tasks to access Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.openai_api_key.arn
        ]
      }
    ]
  })

  tags = var.common_tags
}
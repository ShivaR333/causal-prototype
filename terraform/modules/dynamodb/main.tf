resource "aws_dynamodb_table" "agent_sessions" {
  name           = "agent_sessions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "SessionId"

  attribute {
    name = "SessionId"
    type = "S"
  }

  ttl {
    attribute_name = "ExpiresAt"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-agent-sessions"
    Environment = var.environment
    Project     = var.project_name
  }
}
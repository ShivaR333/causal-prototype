output "websocket_endpoint" {
  description = "WebSocket API Gateway endpoint URL"
  value       = module.apigateway.websocket_endpoint
}

output "state_machine_arn" {
  description = "Step Functions state machine ARN"
  value       = module.stepfunctions.state_machine_arn
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = module.dynamodb.table_name
}

output "rawdata_bucket_name" {
  description = "S3 bucket name for raw data"
  value       = module.s3.rawdata_bucket_name
}

output "artifacts_bucket_name" {
  description = "S3 bucket name for artifacts"
  value       = module.s3.artifacts_bucket_name
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = module.cognito.user_pool_id
}

output "cognito_user_pool_client_id" {
  description = "Cognito User Pool Client ID"
  value       = module.cognito.user_pool_client_id
}

output "ecs_cluster_name" {
  description = "ECS Cluster name"
  value       = module.ecs.cluster_name
}
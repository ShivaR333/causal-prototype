output "websocket_endpoint" {
  description = "WebSocket API Gateway endpoint URL"
  value       = "${aws_apigatewayv2_api.websocket_api.api_endpoint}/${aws_apigatewayv2_stage.websocket_stage.name}"
}

output "websocket_api_id" {
  description = "ID of the WebSocket API"
  value       = aws_apigatewayv2_api.websocket_api.id
}

output "websocket_execution_arn" {
  description = "Execution ARN for the WebSocket API (for IAM policies)"
  value       = aws_apigatewayv2_api.websocket_api.execution_arn
}
output "websocket_handler_arn" {
  description = "ARN of the websocket handler Lambda function"
  value       = aws_lambda_function.websocket_handler.arn
}

output "websocket_handler_invoke_arn" {
  description = "Invoke ARN of the websocket handler Lambda function"
  value       = aws_lambda_function.websocket_handler.invoke_arn
}

output "parse_initial_query_arn" {
  description = "ARN of the parse initial query Lambda function"
  value       = aws_lambda_function.parse_initial_query.arn
}

output "send_prompt_arn" {
  description = "ARN of the send prompt Lambda function"
  value       = aws_lambda_function.send_prompt.arn
}

output "invoke_llm_arn" {
  description = "ARN of the invoke LLM Lambda function"
  value       = aws_lambda_function.invoke_llm.arn
}

output "dispatch_tool_arn" {
  description = "ARN of the dispatch tool Lambda function"
  value       = aws_lambda_function.dispatch_tool.arn
}

output "append_tool_output_arn" {
  description = "ARN of the append tool output Lambda function"
  value       = aws_lambda_function.append_tool_output.arn
}

output "handle_finish_arn" {
  description = "ARN of the handle finish Lambda function"
  value       = aws_lambda_function.handle_finish.arn
}

output "data_query_arn" {
  description = "ARN of the data query Lambda function"
  value       = aws_lambda_function.data_query.arn
}

output "handle_error_arn" {
  description = "ARN of the handle error Lambda function"
  value       = aws_lambda_function.handle_error.arn
}

output "handle_timeout_arn" {
  description = "ARN of the handle timeout Lambda function"
  value       = aws_lambda_function.handle_timeout.arn
}

output "websocket_authorizer_arn" {
  description = "ARN of the WebSocket authorizer Lambda function"
  value       = aws_lambda_function.websocket_authorizer.arn
}

output "websocket_authorizer_invoke_arn" {
  description = "Invoke ARN of the WebSocket authorizer Lambda function"
  value       = aws_lambda_function.websocket_authorizer.invoke_arn
}
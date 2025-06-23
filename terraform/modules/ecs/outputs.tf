output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "eda_repository_url" {
  description = "URL of the EDA ECR repository"
  value       = aws_ecr_repository.eda.repository_url
}

output "analysis_repository_url" {
  description = "URL of the analysis ECR repository"
  value       = aws_ecr_repository.analysis.repository_url
}

output "eda_task_definition_arn" {
  description = "ARN of the EDA task definition"
  value       = aws_ecs_task_definition.eda.arn
}

output "analysis_task_definition_arn" {
  description = "ARN of the analysis task definition"
  value       = aws_ecs_task_definition.analysis.arn
}
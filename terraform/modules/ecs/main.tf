resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-cluster"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_ecr_repository" "eda" {
  name                 = "${var.project_name}-${var.environment}-eda"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-eda"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_ecr_repository" "analysis" {
  name                 = "${var.project_name}-${var.environment}-analysis"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${var.project_name}-${var.environment}-analysis"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_ecs_task_definition" "eda" {
  family                   = "${var.project_name}-${var.environment}-eda"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = var.ecs_task_execution_role
  task_role_arn           = var.ecs_task_role

  container_definitions = jsonencode([
    {
      name  = "eda"
      image = "${aws_ecr_repository.eda.repository_url}:latest"
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.project_name}-${var.environment}-eda"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
      
      environment = [
        {
          name  = "PROJECT_NAME"
          value = var.project_name
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]
    }
  ])

  tags = {
    Name        = "${var.project_name}-${var.environment}-eda"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_ecs_task_definition" "analysis" {
  family                   = "${var.project_name}-${var.environment}-analysis"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = var.ecs_task_execution_role
  task_role_arn           = var.ecs_task_role

  container_definitions = jsonencode([
    {
      name  = "analysis"
      image = "${aws_ecr_repository.analysis.repository_url}:latest"
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/${var.project_name}-${var.environment}-analysis"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }
      
      environment = [
        {
          name  = "PROJECT_NAME"
          value = var.project_name
        },
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]
    }
  ])

  tags = {
    Name        = "${var.project_name}-${var.environment}-analysis"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_cloudwatch_log_group" "eda" {
  name              = "/ecs/${var.project_name}-${var.environment}-eda"
  retention_in_days = 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-eda-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}

resource "aws_cloudwatch_log_group" "analysis" {
  name              = "/ecs/${var.project_name}-${var.environment}-analysis"
  retention_in_days = 7

  tags = {
    Name        = "${var.project_name}-${var.environment}-analysis-logs"
    Environment = var.environment
    Project     = var.project_name
  }
}
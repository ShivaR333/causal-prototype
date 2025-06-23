# Lambda function packages (created by scripts/package-lambdas.sh)
variable "lambda_packages_dir" {
  description = "Directory containing packaged Lambda functions"
  type        = string
  default     = "../../lambda-packages"
}

resource "aws_lambda_function" "websocket_handler" {
  filename         = "${var.lambda_packages_dir}/websocket-handler.zip"
  function_name    = "${var.project_name}-${var.environment}-websocket-handler"
  role            = var.lambda_execution_role
  handler         = "index.lambda_handler"
  source_code_hash = filebase64sha256("${var.lambda_packages_dir}/websocket-handler.zip")
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 128

  environment {
    variables = {
      CONNECTIONS_TABLE_NAME = "${var.project_name}-${var.environment}-connections"
      SESSIONS_TABLE_NAME    = "${var.project_name}-${var.environment}-sessions"
      DYNAMODB_TABLE_NAME    = var.dynamodb_table_name
      RAWDATA_BUCKET_NAME    = var.rawdata_bucket_name
      ARTIFACTS_BUCKET_NAME  = var.artifacts_bucket_name
      OPENAI_SECRET_ARN     = var.openai_secret_arn
      JWT_SECRET_ARN        = var.jwt_secret_arn
      STATE_MACHINE_ARN     = var.step_function_arn
    }
  }
}

resource "aws_lambda_function" "parse_initial_query" {
  filename         = "${var.lambda_packages_dir}/parse-initial-query.zip"
  function_name    = "${var.project_name}-${var.environment}-parse-initial-query"
  role            = var.lambda_execution_role
  handler         = "index.lambda_handler"
  source_code_hash = filebase64sha256("${var.lambda_packages_dir}/parse-initial-query.zip")
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 128

  environment {
    variables = {
      DYNAMODB_TABLE_NAME   = var.dynamodb_table_name
      RAWDATA_BUCKET_NAME   = var.rawdata_bucket_name
      ARTIFACTS_BUCKET_NAME = var.artifacts_bucket_name
    }
  }
}

resource "aws_lambda_function" "send_prompt" {
  filename         = "${var.lambda_packages_dir}/send-prompt.zip"
  function_name    = "${var.project_name}-${var.environment}-send-prompt"
  role            = var.lambda_execution_role
  handler         = "index.lambda_handler"
  source_code_hash = filebase64sha256("${var.lambda_packages_dir}/send-prompt.zip")
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 128

  environment {
    variables = {
      DYNAMODB_TABLE_NAME   = var.dynamodb_table_name
      RAWDATA_BUCKET_NAME   = var.rawdata_bucket_name
      ARTIFACTS_BUCKET_NAME = var.artifacts_bucket_name
    }
  }
}

resource "aws_lambda_function" "invoke_llm" {
  filename         = "${var.lambda_packages_dir}/invoke-llm.zip"
  function_name    = "${var.project_name}-${var.environment}-invoke-llm"
  role            = var.lambda_execution_role
  handler         = "index.lambda_handler"
  source_code_hash = filebase64sha256("${var.lambda_packages_dir}/invoke-llm.zip")
  runtime         = "python3.9"
  timeout         = 300
  memory_size     = 512

  environment {
    variables = {
      DYNAMODB_TABLE_NAME   = var.dynamodb_table_name
      RAWDATA_BUCKET_NAME   = var.rawdata_bucket_name
      ARTIFACTS_BUCKET_NAME = var.artifacts_bucket_name
      OPENAI_SECRET_ARN     = var.openai_secret_arn
      OPENAI_SECRET_NAME    = "${var.project_name}-${var.environment}-openai-api-key"
      JWT_SECRET_ARN        = var.jwt_secret_arn
    }
  }
}

resource "aws_lambda_function" "dispatch_tool" {
  filename         = "${var.lambda_packages_dir}/dispatch-tool.zip"
  function_name    = "${var.project_name}-${var.environment}-dispatch-tool"
  role            = var.lambda_execution_role
  handler         = "index.lambda_handler"
  source_code_hash = filebase64sha256("${var.lambda_packages_dir}/dispatch-tool.zip")
  runtime         = "python3.9"
  timeout         = 60
  memory_size     = 256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME   = var.dynamodb_table_name
      RAWDATA_BUCKET_NAME   = var.rawdata_bucket_name
      ARTIFACTS_BUCKET_NAME = var.artifacts_bucket_name
    }
  }
}

resource "aws_lambda_function" "append_tool_output" {
  filename         = "${var.lambda_packages_dir}/append-tool-output.zip"
  function_name    = "${var.project_name}-${var.environment}-append-tool-output"
  role            = var.lambda_execution_role
  handler         = "index.lambda_handler"
  source_code_hash = filebase64sha256("${var.lambda_packages_dir}/append-tool-output.zip")
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 128

  environment {
    variables = {
      DYNAMODB_TABLE_NAME   = var.dynamodb_table_name
      RAWDATA_BUCKET_NAME   = var.rawdata_bucket_name
      ARTIFACTS_BUCKET_NAME = var.artifacts_bucket_name
    }
  }
}

resource "aws_lambda_function" "handle_finish" {
  filename         = "${var.lambda_packages_dir}/handle-finish.zip"
  function_name    = "${var.project_name}-${var.environment}-handle-finish"
  role            = var.lambda_execution_role
  handler         = "index.lambda_handler"
  source_code_hash = filebase64sha256("${var.lambda_packages_dir}/handle-finish.zip")
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 128

  environment {
    variables = {
      DYNAMODB_TABLE_NAME   = var.dynamodb_table_name
      RAWDATA_BUCKET_NAME   = var.rawdata_bucket_name
      ARTIFACTS_BUCKET_NAME = var.artifacts_bucket_name
    }
  }
}

resource "aws_lambda_function" "data_query" {
  filename         = "${var.lambda_packages_dir}/data-query.zip"
  function_name    = "${var.project_name}-${var.environment}-data-query"
  role            = var.lambda_execution_role
  handler         = "index.lambda_handler"
  source_code_hash = filebase64sha256("${var.lambda_packages_dir}/data-query.zip")
  runtime         = "python3.9"
  timeout         = 60
  memory_size     = 256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME   = var.dynamodb_table_name
      RAWDATA_BUCKET_NAME   = var.rawdata_bucket_name
      ARTIFACTS_BUCKET_NAME = var.artifacts_bucket_name
    }
  }
}

resource "aws_lambda_function" "handle_error" {
  filename         = "${var.lambda_packages_dir}/handle-error.zip"
  function_name    = "${var.project_name}-${var.environment}-handle-error"
  role            = var.lambda_execution_role
  handler         = "index.lambda_handler"
  source_code_hash = filebase64sha256("${var.lambda_packages_dir}/handle-error.zip")
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 128

  environment {
    variables = {
      DYNAMODB_TABLE_NAME   = var.dynamodb_table_name
      RAWDATA_BUCKET_NAME   = var.rawdata_bucket_name
      ARTIFACTS_BUCKET_NAME = var.artifacts_bucket_name
    }
  }
}

resource "aws_lambda_function" "handle_timeout" {
  filename         = "${var.lambda_packages_dir}/handle-timeout.zip"
  function_name    = "${var.project_name}-${var.environment}-handle-timeout"
  role            = var.lambda_execution_role
  handler         = "index.lambda_handler"
  source_code_hash = filebase64sha256("${var.lambda_packages_dir}/handle-timeout.zip")
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 128

  environment {
    variables = {
      DYNAMODB_TABLE_NAME   = var.dynamodb_table_name
      RAWDATA_BUCKET_NAME   = var.rawdata_bucket_name
      ARTIFACTS_BUCKET_NAME = var.artifacts_bucket_name
    }
  }
}

resource "aws_lambda_function" "websocket_authorizer" {
  filename         = "${var.lambda_packages_dir}/websocket-authorizer.zip"
  function_name    = "${var.project_name}-${var.environment}-websocket-authorizer"
  role            = var.lambda_execution_role
  handler         = "index.lambda_handler"
  source_code_hash = filebase64sha256("${var.lambda_packages_dir}/websocket-authorizer.zip")
  runtime         = "python3.9"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      USER_POOL_ID         = var.user_pool_id
      USER_POOL_CLIENT_ID  = var.user_pool_client_id
      JWT_SECRET_ARN       = var.jwt_secret_arn
    }
  }
}
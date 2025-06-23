resource "aws_sfn_state_machine" "agent_sm" {
  name     = "${var.project_name}-${var.environment}-agent-sm"
  role_arn = var.step_functions_role_arn

  definition = jsonencode({
    Comment = "Agent State Machine for REACT loop"
    StartAt = "ParseInitialQuery"
    States = {
      ParseInitialQuery = {
        Type     = "Task"
        Resource = var.parse_query_lambda_arn
        Next     = "InvokeLLM"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "HandleError"
          }
        ]
      }
      InvokeLLM = {
        Type     = "Task"
        Resource = var.invoke_llm_lambda_arn
        Next     = "CheckResponse"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "HandleError"
          }
        ]
      }
      CheckResponse = {
        Type = "Choice"
        Choices = [
          {
            Variable     = "$.response_type"
            StringEquals = "tool_call"
            Next         = "DispatchTool"
          },
          {
            Variable     = "$.response_type"
            StringEquals = "user_prompt"
            Next         = "SendPrompt"
          }
        ]
        Default = "HandleFinish"
      }
      SendPrompt = {
        Type     = "Task"
        Resource = var.send_prompt_lambda_arn
        Parameters = {
          "TaskToken.$" = "$$.Task.Token"
          "Input.$"     = "$"
        }
        Next = "InvokeLLM"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "HandleError"
          }
        ]
      }
      DispatchTool = {
        Type = "Choice"
        Choices = [
          {
            Variable     = "$.tool_name"
            StringEquals = "eda_analysis"
            Next         = "RunEDATask"
          },
          {
            Variable     = "$.tool_name"
            StringEquals = "causal_analysis"
            Next         = "RunAnalysisTask"
          }
        ]
        Default = "DispatchToolLambda"
      }
      DispatchToolLambda = {
        Type     = "Task"
        Resource = var.dispatch_tool_lambda_arn
        Next     = "AppendToolOutput"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "HandleError"
          }
        ]
      }
      RunEDATask = {
        Type     = "Task"
        Resource = "arn:aws:states:::ecs:runTask.sync"
        Parameters = {
          TaskDefinition = var.eda_task_definition_arn
          Cluster        = var.ecs_cluster_arn
          LaunchType     = "FARGATE"
          NetworkConfiguration = {
            AwsvpcConfiguration = {
              Subnets        = var.private_subnet_ids
              SecurityGroups = [var.ecs_security_group_id]
              AssignPublicIp = "DISABLED"
            }
          }
        }
        Next = "AppendToolOutput"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "HandleError"
          }
        ]
      }
      RunAnalysisTask = {
        Type     = "Task"
        Resource = "arn:aws:states:::ecs:runTask.sync"
        Parameters = {
          TaskDefinition = var.analysis_task_definition_arn
          Cluster        = var.ecs_cluster_arn
          LaunchType     = "FARGATE"
          NetworkConfiguration = {
            AwsvpcConfiguration = {
              Subnets        = var.private_subnet_ids
              SecurityGroups = [var.ecs_security_group_id]
              AssignPublicIp = "DISABLED"
            }
          }
        }
        Next = "AppendToolOutput"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "HandleError"
          }
        ]
      }
      AppendToolOutput = {
        Type     = "Task"
        Resource = var.append_output_lambda_arn
        Next     = "InvokeLLM"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "HandleError"
          }
        ]
      }
      HandleFinish = {
        Type     = "Task"
        Resource = var.handle_finish_lambda_arn
        End      = true
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            Next        = "HandleError"
          }
        ]
      }
      HandleError = {
        Type     = "Task"
        Resource = var.handle_error_lambda_arn
        End      = true
      }
    }
  })

  tags = {
    Name        = "${var.project_name}-${var.environment}-agent-sm"
    Environment = var.environment
    Project     = var.project_name
  }
}
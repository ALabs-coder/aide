# Lambda Functions for PDF Extractor API - Layer-based Architecture
# Uses pre-built function packages and Lambda layers for dependencies

# API Lambda function
resource "aws_lambda_function" "api" {
  filename         = "${var.functions_dir}/api.zip"
  function_name    = "${var.name_prefix}-api"
  role            = var.lambda_role_arn
  handler         = "handler.handler"
  source_code_hash = filebase64sha256("${var.functions_dir}/api.zip")
  runtime         = "python3.11"
  timeout         = 180
  memory_size     = 512

  # Lambda layers for dependencies
  layers = var.api_lambda_layers

  # Environment variables
  environment {
    variables = merge(var.environment_variables, {
      ENVIRONMENT = "dev"
      FUNCTION_TYPE = "api"
    })
  }

  # Dead letter queue configuration
  dead_letter_config {
    target_arn = var.dlq_arn
  }

  # Reserved concurrency
  reserved_concurrent_executions = 5

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-api"
    Type = "Lambda"
    Architecture = "layers"
  })
}

# Upload Lambda function
resource "aws_lambda_function" "upload" {
  filename         = "${var.functions_dir}/upload.zip"
  function_name    = "${var.name_prefix}-upload"
  role            = var.lambda_role_arn
  handler         = "handler.handler"
  source_code_hash = filebase64sha256("${var.functions_dir}/upload.zip")
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 1024

  # Lambda layers for dependencies
  layers = var.api_lambda_layers

  # Environment variables
  environment {
    variables = merge(var.environment_variables, {
      ENVIRONMENT = "dev"
      FUNCTION_TYPE = "upload"
    })
  }

  # Dead letter queue configuration
  dead_letter_config {
    target_arn = var.dlq_arn
  }

  # Reserved concurrency
  reserved_concurrent_executions = 3

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-upload"
    Type = "Lambda"
    Architecture = "layers"
  })
}

# Statement Data Lambda function
resource "aws_lambda_function" "statement_data" {
  filename         = "${var.functions_dir}/statement_data.zip"
  function_name    = "${var.name_prefix}-statement-data"
  role            = var.lambda_role_arn
  handler         = "handler.handler"
  source_code_hash = filebase64sha256("${var.functions_dir}/statement_data.zip")
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 256

  # Lambda layers for dependencies
  layers = var.api_lambda_layers

  # Environment variables
  environment {
    variables = merge(var.environment_variables, {
      ENVIRONMENT = "dev"
      FUNCTION_TYPE = "statement_data"
    })
  }

  # Dead letter queue configuration
  dead_letter_config {
    target_arn = var.dlq_arn
  }

  # Reserved concurrency
  reserved_concurrent_executions = 5

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-statement-data"
    Type = "Lambda"
    Architecture = "layers"
  })
}

# CloudWatch log group for API Lambda
resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/lambda/${aws_lambda_function.api.function_name}"
  retention_in_days = 7

  tags = var.tags
}

# CloudWatch log group for Upload Lambda
resource "aws_cloudwatch_log_group" "upload" {
  name              = "/aws/lambda/${aws_lambda_function.upload.function_name}"
  retention_in_days = 7

  tags = var.tags
}

# CloudWatch log group for Statement Data Lambda
resource "aws_cloudwatch_log_group" "statement_data" {
  name              = "/aws/lambda/${aws_lambda_function.statement_data.function_name}"
  retention_in_days = 7

  tags = var.tags
}

# Excel Export Lambda function
resource "aws_lambda_function" "excel_export" {
  filename         = "${var.functions_dir}/excel_export.zip"
  function_name    = "${var.name_prefix}-excel-export"
  role            = var.lambda_role_arn
  handler         = "handler.handler"
  source_code_hash = filebase64sha256("${var.functions_dir}/excel_export.zip")
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 256

  # Lambda layers for dependencies
  layers = var.api_lambda_layers

  # Environment variables
  environment {
    variables = merge(var.environment_variables, {
      ENVIRONMENT = "dev"
      FUNCTION_TYPE = "excel_export"
    })
  }

  # Dead letter queue configuration
  dead_letter_config {
    target_arn = var.dlq_arn
  }

  # Reserved concurrency
  reserved_concurrent_executions = 5

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-excel-export"
    Type = "Lambda"
    Architecture = "layers"
  })
}

# CloudWatch log group for Excel Export Lambda
resource "aws_cloudwatch_log_group" "excel_export" {
  name              = "/aws/lambda/${aws_lambda_function.excel_export.function_name}"
  retention_in_days = 7

  tags = var.tags
}

# PDF Viewer Lambda function
resource "aws_lambda_function" "pdf_viewer" {
  filename         = "${var.functions_dir}/pdf_viewer.zip"
  function_name    = "${var.name_prefix}-pdf-viewer"
  role            = var.lambda_role_arn
  handler         = "handler.handler"
  source_code_hash = filebase64sha256("${var.functions_dir}/pdf_viewer.zip")
  runtime         = "python3.11"
  timeout         = 180
  memory_size     = 1024

  # Lambda layers for dependencies
  layers = var.api_lambda_layers

  # Environment variables
  environment {
    variables = merge(var.environment_variables, {
      ENVIRONMENT = "dev"
      FUNCTION_TYPE = "pdf_viewer"
    })
  }

  # Dead letter queue configuration
  dead_letter_config {
    target_arn = var.dlq_arn
  }

  # Reserved concurrency
  reserved_concurrent_executions = 5

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-pdf-viewer"
    Type = "Lambda"
    Architecture = "layers"
  })
}

# CloudWatch log group for PDF Viewer Lambda
resource "aws_cloudwatch_log_group" "pdf_viewer" {
  name              = "/aws/lambda/${aws_lambda_function.pdf_viewer.function_name}"
  retention_in_days = 7

  tags = var.tags
}

# Processor Lambda function
resource "aws_lambda_function" "processor" {
  filename         = "${var.functions_dir}/processor.zip"
  function_name    = "${var.name_prefix}-processor"
  role            = var.lambda_role_arn
  handler         = "handler.handler"
  source_code_hash = filebase64sha256("${var.functions_dir}/processor.zip")
  runtime         = "python3.11"
  timeout         = 600
  memory_size     = 1024

  # Lambda layers for dependencies
  layers = var.processor_lambda_layers

  # Environment variables
  environment {
    variables = merge(var.environment_variables, {
      ENVIRONMENT = "dev"
      FUNCTION_TYPE = "processor"
    })
  }

  # Dead letter queue configuration
  dead_letter_config {
    target_arn = var.dlq_arn
  }

  # Reserved concurrency
  reserved_concurrent_executions = 2

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-processor"
    Type = "Lambda"
    Architecture = "layers"
  })
}

# CloudWatch log group for Processor Lambda
resource "aws_cloudwatch_log_group" "processor" {
  name              = "/aws/lambda/${aws_lambda_function.processor.function_name}"
  retention_in_days = 7

  tags = var.tags
}

# Event source mapping for processor Lambda (SQS trigger)
resource "aws_lambda_event_source_mapping" "processor_sqs" {
  event_source_arn = var.processing_queue_arn
  function_name    = aws_lambda_function.processor.arn
  batch_size       = 1
  
  # Only process messages when Lambda is not throttled
  maximum_batching_window_in_seconds = 5
}

# Cleanup Lambda function
resource "aws_lambda_function" "cleanup" {
  filename         = "${var.functions_dir}/cleanup.zip"
  function_name    = "${var.name_prefix}-cleanup"
  role            = var.lambda_role_arn
  handler         = "handler.handler"
  source_code_hash = filebase64sha256("${var.functions_dir}/cleanup.zip")
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 256

  # Lambda layers for dependencies
  layers = var.processor_lambda_layers

  # Environment variables
  environment {
    variables = merge(var.environment_variables, {
      ENVIRONMENT = "dev"
      FUNCTION_TYPE = "cleanup"
      CLEANUP_DAYS = "30"
    })
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cleanup"
    Type = "Lambda"
    Architecture = "layers"
  })
}

# CloudWatch log group for Cleanup Lambda
resource "aws_cloudwatch_log_group" "cleanup" {
  name              = "/aws/lambda/${aws_lambda_function.cleanup.function_name}"
  retention_in_days = 7

  tags = var.tags
}

# CloudWatch event rule for cleanup (runs daily)
resource "aws_cloudwatch_event_rule" "cleanup_schedule" {
  name                = "${var.name_prefix}-cleanup-schedule"
  description         = "Daily cleanup of old files and records"
  schedule_expression = "cron(0 2 * * ? *)"  # Run at 2 AM UTC daily

  tags = var.tags
}

# CloudWatch event target for cleanup Lambda
resource "aws_cloudwatch_event_target" "cleanup_target" {
  rule      = aws_cloudwatch_event_rule.cleanup_schedule.name
  target_id = "CleanupTarget"
  arn       = aws_lambda_function.cleanup.arn
}

# Permission for CloudWatch to invoke cleanup Lambda
resource "aws_lambda_permission" "allow_cloudwatch_cleanup" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.cleanup.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cleanup_schedule.arn
}

# DLQ Processor Lambda function
resource "aws_lambda_function" "dlq_processor" {
  filename         = "${var.functions_dir}/dlq_processor.zip"
  function_name    = "${var.name_prefix}-dlq-processor"
  role            = var.lambda_role_arn
  handler         = "handler.handler"
  source_code_hash = filebase64sha256("${var.functions_dir}/dlq_processor.zip")
  runtime         = "python3.11"
  timeout         = 300
  memory_size     = 512

  # Lambda layers for dependencies
  layers = var.processor_lambda_layers

  # Environment variables
  environment {
    variables = merge(var.environment_variables, {
      ENVIRONMENT = "dev"
      FUNCTION_TYPE = "dlq_processor"
      MAX_RETRY_COUNT = "3"
      ALERT_SNS_TOPIC = var.alert_sns_topic_arn
    })
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-dlq-processor"
    Type = "Lambda"
    Architecture = "layers"
  })
}

# CloudWatch log group for DLQ Processor Lambda
resource "aws_cloudwatch_log_group" "dlq_processor" {
  name              = "/aws/lambda/${aws_lambda_function.dlq_processor.function_name}"
  retention_in_days = 7

  tags = var.tags
}

# Event source mapping for DLQ processor Lambda
resource "aws_lambda_event_source_mapping" "dlq_processor_sqs" {
  event_source_arn = var.dlq_arn
  function_name    = aws_lambda_function.dlq_processor.arn
  batch_size       = 1

  # Process messages from DLQ less frequently
  maximum_batching_window_in_seconds = 60
}


# Lambda Module Outputs

output "functions" {
  description = "Lambda functions information"
  value = {
    api = {
      name        = aws_lambda_function.api.function_name
      arn         = aws_lambda_function.api.arn
      invoke_arn  = aws_lambda_function.api.invoke_arn
      version     = aws_lambda_function.api.version
    }
    processor = {
      name        = aws_lambda_function.processor.function_name
      arn         = aws_lambda_function.processor.arn
      invoke_arn  = aws_lambda_function.processor.invoke_arn
      version     = aws_lambda_function.processor.version
    }
    cleanup = {
      name        = aws_lambda_function.cleanup.function_name
      arn         = aws_lambda_function.cleanup.arn
      invoke_arn  = aws_lambda_function.cleanup.invoke_arn
      version     = aws_lambda_function.cleanup.version
    }
    dlq_processor = {
      name        = aws_lambda_function.dlq_processor.function_name
      arn         = aws_lambda_function.dlq_processor.arn
      invoke_arn  = aws_lambda_function.dlq_processor.invoke_arn
      version     = aws_lambda_function.dlq_processor.version
    }
  }
}

output "api_lambda" {
  description = "API Lambda function details"
  value = {
    name        = aws_lambda_function.api.function_name
    arn         = aws_lambda_function.api.arn
    invoke_arn  = aws_lambda_function.api.invoke_arn
  }
}

output "processor_lambda" {
  description = "Processor Lambda function details"
  value = {
    name        = aws_lambda_function.processor.function_name
    arn         = aws_lambda_function.processor.arn
    invoke_arn  = aws_lambda_function.processor.invoke_arn
  }
}

output "cleanup_lambda" {
  description = "Cleanup Lambda function details"
  value = {
    name        = aws_lambda_function.cleanup.function_name
    arn         = aws_lambda_function.cleanup.arn
    invoke_arn  = aws_lambda_function.cleanup.invoke_arn
  }
}

output "dlq_processor_lambda" {
  description = "DLQ Processor Lambda function details"
  value = {
    name        = aws_lambda_function.dlq_processor.function_name
    arn         = aws_lambda_function.dlq_processor.arn
    invoke_arn  = aws_lambda_function.dlq_processor.invoke_arn
  }
}

output "log_groups" {
  description = "CloudWatch log groups"
  value = {
    api           = aws_cloudwatch_log_group.api.name
    processor     = aws_cloudwatch_log_group.processor.name
    cleanup       = aws_cloudwatch_log_group.cleanup.name
    dlq_processor = aws_cloudwatch_log_group.dlq_processor.name
  }
}
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
    upload = {
      name        = aws_lambda_function.upload.function_name
      arn         = aws_lambda_function.upload.arn
      invoke_arn  = aws_lambda_function.upload.invoke_arn
      version     = aws_lambda_function.upload.version
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
    statement_data = {
      name        = aws_lambda_function.statement_data.function_name
      arn         = aws_lambda_function.statement_data.arn
      invoke_arn  = aws_lambda_function.statement_data.invoke_arn
      version     = aws_lambda_function.statement_data.version
    }
    pdf_viewer = {
      name        = aws_lambda_function.pdf_viewer.function_name
      arn         = aws_lambda_function.pdf_viewer.arn
      invoke_arn  = aws_lambda_function.pdf_viewer.invoke_arn
      version     = aws_lambda_function.pdf_viewer.version
    }
    csv_export = {
      name        = aws_lambda_function.csv_export.function_name
      arn         = aws_lambda_function.csv_export.arn
      invoke_arn  = aws_lambda_function.csv_export.invoke_arn
      version     = aws_lambda_function.csv_export.version
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

output "upload_lambda" {
  description = "Upload Lambda function details"
  value = {
    name        = aws_lambda_function.upload.function_name
    arn         = aws_lambda_function.upload.arn
    invoke_arn  = aws_lambda_function.upload.invoke_arn
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
    upload        = aws_cloudwatch_log_group.upload.name
    processor     = aws_cloudwatch_log_group.processor.name
    cleanup       = aws_cloudwatch_log_group.cleanup.name
    dlq_processor = aws_cloudwatch_log_group.dlq_processor.name
    statement_data = aws_cloudwatch_log_group.statement_data.name
    pdf_viewer = aws_cloudwatch_log_group.pdf_viewer.name
    csv_export = aws_cloudwatch_log_group.csv_export.name
  }
}

output "statement_data_lambda" {
  description = "Statement Data Lambda function details"
  value = {
    name        = aws_lambda_function.statement_data.function_name
    arn         = aws_lambda_function.statement_data.arn
    invoke_arn  = aws_lambda_function.statement_data.invoke_arn
  }
}

output "csv_export_lambda" {
  description = "CSV Export Lambda function details"
  value = {
    name        = aws_lambda_function.csv_export.function_name
    arn         = aws_lambda_function.csv_export.arn
    invoke_arn  = aws_lambda_function.csv_export.invoke_arn
  }
}
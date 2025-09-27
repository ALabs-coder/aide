# API Gateway for PDF Extractor API

# IAM role for API Gateway CloudWatch Logs
resource "aws_iam_role" "api_gateway_cloudwatch" {
  name = "${var.name_prefix}-api-gateway-cloudwatch"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Attach policy for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch" {
  role       = aws_iam_role.api_gateway_cloudwatch.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# Set the CloudWatch Logs role for API Gateway at account level
resource "aws_api_gateway_account" "api" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn
}

# REST API
resource "aws_api_gateway_rest_api" "api" {
  name        = "${var.name_prefix}-api"
  description = "PDF Extractor API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  # Enable binary media types for file uploads
  binary_media_types = [
    "application/pdf",
    "application/x-pdf",
    "multipart/form-data"
  ]

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-api"
    Type = "API-Gateway"
  })
}

# API Gateway deployment
resource "aws_api_gateway_deployment" "api" {
  depends_on = [
    aws_api_gateway_method.statements_method,
    aws_api_gateway_method.upload_method,
    aws_api_gateway_method.statements_data_method,
    aws_api_gateway_method.statements_excel_method,
    aws_api_gateway_method.pdf_method,
    aws_api_gateway_method.configurations_banks_method,
    aws_api_gateway_method.proxy_method,
    aws_api_gateway_method.proxy_root_method,
    aws_api_gateway_method.cors_statements_method,
    aws_api_gateway_method.cors_upload_method,
    aws_api_gateway_method.cors_statements_data_method,
    aws_api_gateway_method.cors_statements_excel_method,
    aws_api_gateway_method.cors_pdf_method,
    aws_api_gateway_method.cors_configurations_banks_method,
    aws_api_gateway_method.cors_method,
    aws_api_gateway_method.cors_root_method,
    aws_api_gateway_integration.statements_integration,
    aws_api_gateway_integration.upload_integration,
    aws_api_gateway_integration.statements_data_integration,
    aws_api_gateway_integration.statements_excel_integration,
    aws_api_gateway_integration.pdf_integration,
    aws_api_gateway_integration.configurations_banks_integration,
    aws_api_gateway_integration.proxy_integration,
    aws_api_gateway_integration.proxy_root_integration,
    aws_api_gateway_integration.cors_statements_integration,
    aws_api_gateway_integration.cors_upload_integration,
    aws_api_gateway_integration.cors_statements_data_integration,
    aws_api_gateway_integration.cors_statements_excel_integration,
    aws_api_gateway_integration.cors_pdf_integration,
    aws_api_gateway_integration.cors_configurations_banks_integration,
    aws_api_gateway_integration.cors_integration,
    aws_api_gateway_integration.cors_root_integration,
  ]

  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.statements.id,
      aws_api_gateway_resource.upload.id,
      aws_api_gateway_resource.statements_data.id,
      aws_api_gateway_resource.statements_excel.id,
      aws_api_gateway_resource.statements_excel_job_id.id,
      aws_api_gateway_resource.pdf.id,
      aws_api_gateway_resource.pdf_job_id.id,
      aws_api_gateway_resource.configurations.id,
      aws_api_gateway_resource.configurations_banks.id,
      aws_api_gateway_resource.proxy.id,
      aws_api_gateway_method.statements_method.id,
      aws_api_gateway_method.upload_method.id,
      aws_api_gateway_method.statements_data_method.id,
      aws_api_gateway_method.statements_excel_method.id,
      aws_api_gateway_method.pdf_method.id,
      aws_api_gateway_method.configurations_banks_method.id,
      aws_api_gateway_method.proxy_method.id,
      aws_api_gateway_method.proxy_root_method.id,
      aws_api_gateway_method.cors_statements_method.id,
      aws_api_gateway_method.cors_upload_method.id,
      aws_api_gateway_method.cors_statements_data_method.id,
      aws_api_gateway_method.cors_statements_excel_method.id,
      aws_api_gateway_method.cors_pdf_method.id,
      aws_api_gateway_method.cors_configurations_banks_method.id,
      aws_api_gateway_method.cors_method.id,
      aws_api_gateway_method.cors_root_method.id,
      aws_api_gateway_integration.statements_integration.id,
      aws_api_gateway_integration.upload_integration.id,
      aws_api_gateway_integration.statements_data_integration.id,
      aws_api_gateway_integration.statements_excel_integration.id,
      aws_api_gateway_integration.pdf_integration.id,
      aws_api_gateway_integration.configurations_banks_integration.id,
      aws_api_gateway_integration.proxy_integration.id,
      aws_api_gateway_integration.proxy_root_integration.id,
      aws_api_gateway_integration.cors_statements_integration.id,
      aws_api_gateway_integration.cors_upload_integration.id,
      aws_api_gateway_integration.cors_statements_data_integration.id,
      aws_api_gateway_integration.cors_statements_excel_integration.id,
      aws_api_gateway_integration.cors_pdf_integration.id,
      aws_api_gateway_integration.cors_configurations_banks_integration.id,
      aws_api_gateway_integration.cors_integration.id,
      aws_api_gateway_integration.cors_root_integration.id,
      # Include Lambda source code hashes to trigger redeployment when functions change
      var.lambda_source_code_hashes,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway stage
resource "aws_api_gateway_stage" "api" {
  deployment_id = aws_api_gateway_deployment.api.id
  rest_api_id   = aws_api_gateway_rest_api.api.id
  stage_name    = var.stage_name

  # Enable logging
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      error          = "$context.error.message"
      errorValidation = "$context.error.validationErrorString"
    })
  }

  tags = var.tags

  # Ensure the CloudWatch Logs role is set up before creating the stage
  depends_on = [aws_api_gateway_account.api]
}

# CloudWatch log group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.name_prefix}-api"
  retention_in_days = 7

  tags = var.tags
}

# Method settings for the stage
resource "aws_api_gateway_method_settings" "api" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = aws_api_gateway_stage.api.stage_name
  method_path = "*/*"

  settings {
    logging_level      = "INFO"
    data_trace_enabled = false
    metrics_enabled    = true

    # Throttling settings
    throttling_rate_limit  = 100
    throttling_burst_limit = 50
  }
}

# Statements resource
resource "aws_api_gateway_resource" "statements" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "statements"
}


# Upload resource
resource "aws_api_gateway_resource" "upload" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "upload"
}

# Statement data resource directly under statements (for query parameters)
resource "aws_api_gateway_resource" "statements_data" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.statements.id
  path_part   = "data"
}

# Excel export resource under statements
resource "aws_api_gateway_resource" "statements_excel" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.statements.id
  path_part   = "excel"
}

# Excel job_id resource (for path parameter)
resource "aws_api_gateway_resource" "statements_excel_job_id" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.statements_excel.id
  path_part   = "{job_id}"
}

# PDF resource
resource "aws_api_gateway_resource" "pdf" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "pdf"
}

# PDF job_id resource (for path parameter)
resource "aws_api_gateway_resource" "pdf_job_id" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.pdf.id
  path_part   = "{job_id}"
}


# Configurations resource
resource "aws_api_gateway_resource" "configurations" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "configurations"
}

# Banks resource under configurations
resource "aws_api_gateway_resource" "configurations_banks" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.configurations.id
  path_part   = "banks"
}

# Proxy resource to capture all paths
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "{proxy+}"
}

# Method for statements resource (GET method)
resource "aws_api_gateway_method" "statements_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.statements.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = true
}

# Method for upload resource (POST method)
resource "aws_api_gateway_method" "upload_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.upload.id
  http_method   = "POST"
  authorization = "NONE"
  api_key_required = true
}

# Method for statements data resource (GET method)
resource "aws_api_gateway_method" "statements_data_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.statements_data.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = true
}

# Method for Excel export resource (GET method)
resource "aws_api_gateway_method" "statements_excel_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.statements_excel_job_id.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = true
}

# Method for PDF resource (GET method)
resource "aws_api_gateway_method" "pdf_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.pdf_job_id.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = true

  request_parameters = {
    "method.request.path.job_id" = true
  }
}

# Method for configurations/banks resource (GET method)
resource "aws_api_gateway_method" "configurations_banks_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.configurations_banks.id
  http_method   = "GET"
  authorization = "NONE"
  api_key_required = true
}


# Method for proxy resource (ANY method)
resource "aws_api_gateway_method" "proxy_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"
  api_key_required = true

  # Enable CORS preflight
  request_parameters = {
    "method.request.path.proxy" = true
  }
}

# Method for root resource
resource "aws_api_gateway_method" "proxy_root_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_rest_api.api.root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
  api_key_required = true
}

# Integration for statements resource
resource "aws_api_gateway_integration" "statements_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_method.statements_method.resource_id
  http_method = aws_api_gateway_method.statements_method.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.lambda_invoke_arn

  # Timeout configuration
  timeout_milliseconds = 29000
}

# Integration for upload resource
resource "aws_api_gateway_integration" "upload_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_method.upload_method.resource_id
  http_method = aws_api_gateway_method.upload_method.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.upload_lambda_invoke_arn

  # Timeout configuration
  timeout_milliseconds = 29000
}

# Integration for statements data resource
resource "aws_api_gateway_integration" "statements_data_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_method.statements_data_method.resource_id
  http_method = aws_api_gateway_method.statements_data_method.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.statement_data_lambda_invoke_arn

  # Timeout configuration
  timeout_milliseconds = 29000
}

# Integration for Excel export resource
resource "aws_api_gateway_integration" "statements_excel_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_method.statements_excel_method.resource_id
  http_method = aws_api_gateway_method.statements_excel_method.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.excel_export_lambda_invoke_arn

  # Timeout configuration
  timeout_milliseconds = 29000
}

# Integration for PDF resource
resource "aws_api_gateway_integration" "pdf_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_method.pdf_method.resource_id
  http_method = aws_api_gateway_method.pdf_method.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.pdf_viewer_lambda_invoke_arn

  # Timeout configuration
  timeout_milliseconds = 29000
}

# Integration for configurations/banks resource
resource "aws_api_gateway_integration" "configurations_banks_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_method.configurations_banks_method.resource_id
  http_method = aws_api_gateway_method.configurations_banks_method.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.lambda_invoke_arn

  # Timeout configuration
  timeout_milliseconds = 29000
}


# Integration for proxy resource
resource "aws_api_gateway_integration" "proxy_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_method.proxy_method.resource_id
  http_method = aws_api_gateway_method.proxy_method.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.lambda_invoke_arn

  # Timeout configuration
  timeout_milliseconds = 29000
}

# Integration for root resource
resource "aws_api_gateway_integration" "proxy_root_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_method.proxy_root_method.resource_id
  http_method = aws_api_gateway_method.proxy_root_method.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = var.lambda_invoke_arn

  # Timeout configuration
  timeout_milliseconds = 29000
}

# Lambda permission for API Gateway
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

# Lambda permission for Upload API Gateway
resource "aws_lambda_permission" "upload_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.upload_lambda_function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

# Lambda permission for statements data endpoint
resource "aws_lambda_permission" "statements_data_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.statement_data_lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/GET/statements/data"
}

# Lambda permission for Excel export endpoint
resource "aws_lambda_permission" "excel_export_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.excel_export_lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/GET/statements/excel/*"
}

# Lambda permission for PDF viewer endpoint
resource "aws_lambda_permission" "pdf_viewer_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = var.pdf_viewer_lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/GET/pdf/*"
}


# CORS configuration for statements endpoint
resource "aws_api_gateway_method" "cors_statements_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.statements.id
  http_method   = "OPTIONS"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_integration" "cors_statements_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.statements.id
  http_method = aws_api_gateway_method.cors_statements_method.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "cors_statements_method_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.statements.id
  http_method = aws_api_gateway_method.cors_statements_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "cors_statements_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.statements.id
  http_method = aws_api_gateway_method.cors_statements_method.http_method
  status_code = aws_api_gateway_method_response.cors_statements_method_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS configuration for upload endpoint
resource "aws_api_gateway_method" "cors_upload_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.upload.id
  http_method   = "OPTIONS"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_integration" "cors_upload_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.upload.id
  http_method = aws_api_gateway_method.cors_upload_method.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "cors_upload_method_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.upload.id
  http_method = aws_api_gateway_method.cors_upload_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "cors_upload_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.upload.id
  http_method = aws_api_gateway_method.cors_upload_method.http_method
  status_code = aws_api_gateway_method_response.cors_upload_method_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With'"
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS configuration for statements data endpoint
resource "aws_api_gateway_method" "cors_statements_data_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.statements_data.id
  http_method   = "OPTIONS"
  authorization = "NONE"
  api_key_required = false
}

# CORS configuration for Excel export endpoint
resource "aws_api_gateway_method" "cors_statements_excel_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.statements_excel_job_id.id
  http_method   = "OPTIONS"
  authorization = "NONE"
  api_key_required = false
}

# CORS configuration for PDF endpoint
resource "aws_api_gateway_method" "cors_pdf_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.pdf_job_id.id
  http_method   = "OPTIONS"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_integration" "cors_statements_data_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.statements_data.id
  http_method = aws_api_gateway_method.cors_statements_data_method.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "cors_statements_data_method_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.statements_data.id
  http_method = aws_api_gateway_method.cors_statements_data_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "cors_statements_data_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.statements_data.id
  http_method = aws_api_gateway_method.cors_statements_data_method.http_method
  status_code = aws_api_gateway_method_response.cors_statements_data_method_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS integration for Excel export endpoint
resource "aws_api_gateway_integration" "cors_statements_excel_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.statements_excel_job_id.id
  http_method = aws_api_gateway_method.cors_statements_excel_method.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "cors_statements_excel_method_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.statements_excel_job_id.id
  http_method = aws_api_gateway_method.cors_statements_excel_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "cors_statements_excel_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.statements_excel_job_id.id
  http_method = aws_api_gateway_method.cors_statements_excel_method.http_method
  status_code = aws_api_gateway_method_response.cors_statements_excel_method_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS integration for PDF endpoint
resource "aws_api_gateway_integration" "cors_pdf_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.pdf_job_id.id
  http_method = aws_api_gateway_method.cors_pdf_method.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "cors_pdf_method_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.pdf_job_id.id
  http_method = aws_api_gateway_method.cors_pdf_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "cors_pdf_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.pdf_job_id.id
  http_method = aws_api_gateway_method.cors_pdf_method.http_method
  status_code = aws_api_gateway_method_response.cors_pdf_method_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS configuration for configurations/banks endpoint
resource "aws_api_gateway_method" "cors_configurations_banks_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.configurations_banks.id
  http_method   = "OPTIONS"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_integration" "cors_configurations_banks_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.configurations_banks.id
  http_method = aws_api_gateway_method.cors_configurations_banks_method.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "cors_configurations_banks_method_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.configurations_banks.id
  http_method = aws_api_gateway_method.cors_configurations_banks_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "cors_configurations_banks_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.configurations_banks.id
  http_method = aws_api_gateway_method.cors_configurations_banks_method.http_method
  status_code = aws_api_gateway_method_response.cors_configurations_banks_method_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}


# CORS configuration for preflight requests
resource "aws_api_gateway_method" "cors_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "OPTIONS"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_integration" "cors_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.cors_method.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "cors_method_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.cors_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "cors_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.cors_method.http_method
  status_code = aws_api_gateway_method_response.cors_method_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With'"
    "method.response.header.Access-Control-Allow-Methods" = "'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# CORS configuration for root resource
resource "aws_api_gateway_method" "cors_root_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_rest_api.api.root_resource_id
  http_method   = "OPTIONS"
  authorization = "NONE"
  api_key_required = false
}

resource "aws_api_gateway_integration" "cors_root_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_rest_api.api.root_resource_id
  http_method = aws_api_gateway_method.cors_root_method.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({
      statusCode = 200
    })
  }
}

resource "aws_api_gateway_method_response" "cors_root_method_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_rest_api.api.root_resource_id
  http_method = aws_api_gateway_method.cors_root_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "cors_root_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_rest_api.api.root_resource_id
  http_method = aws_api_gateway_method.cors_root_method.http_method
  status_code = aws_api_gateway_method_response.cors_root_method_response.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Requested-With'"
    "method.response.header.Access-Control-Allow-Methods" = "'DELETE,GET,HEAD,OPTIONS,PATCH,POST,PUT'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}


# Usage plan for rate limiting
resource "aws_api_gateway_usage_plan" "api" {
  name = "${var.name_prefix}-usage-plan"

  api_stages {
    api_id = aws_api_gateway_rest_api.api.id
    stage  = aws_api_gateway_stage.api.stage_name
  }

  quota_settings {
    limit  = 1000
    period = "DAY"
  }

  throttle_settings {
    rate_limit  = 100
    burst_limit = 50
  }

  tags = var.tags
}

# API Key for authentication
resource "aws_api_gateway_api_key" "api_key" {
  name        = "${var.name_prefix}-api-key"
  description = "API key for PDF Extractor API"

  tags = var.tags
}

# Associate API key with usage plan
resource "aws_api_gateway_usage_plan_key" "api_key_association" {
  key_id        = aws_api_gateway_api_key.api_key.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.api.id
}
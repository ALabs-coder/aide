# API Gateway for PDF Extractor API

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
    aws_api_gateway_method.proxy_method,
    aws_api_gateway_method.proxy_root_method,
    aws_api_gateway_integration.proxy_integration,
    aws_api_gateway_integration.proxy_root_integration,
  ]

  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.proxy.id,
      aws_api_gateway_method.proxy_method.id,
      aws_api_gateway_method.proxy_root_method.id,
      aws_api_gateway_integration.proxy_integration.id,
      aws_api_gateway_integration.proxy_root_integration.id,
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
  stage_name    = "dev"

  # Enable logging
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$requestId"
      ip             = "$requestId"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$requestTime"
      httpMethod     = "$httpMethod"
      resourcePath   = "$resourcePath"
      status         = "$status"
      protocol       = "$protocol"
      responseLength = "$responseLength"
      error          = "$error.message"
      errorValidation = "$error.validationErrorString"
    })
  }

  tags = var.tags
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
    data_trace_enabled = true
    metrics_enabled    = true

    # Throttling settings
    throttling_rate_limit  = 100
    throttling_burst_limit = 50
  }
}

# Proxy resource to capture all paths
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "{proxy+}"
}

# Method for proxy resource (ANY method)
resource "aws_api_gateway_method" "proxy_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"

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

# CORS configuration for preflight requests
resource "aws_api_gateway_method" "cors_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "OPTIONS"
  authorization = "NONE"
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
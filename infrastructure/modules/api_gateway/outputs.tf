# API Gateway Module Outputs

output "api_gateway" {
  description = "API Gateway information"
  value = {
    id               = aws_api_gateway_rest_api.api.id
    name             = aws_api_gateway_rest_api.api.name
    root_resource_id = aws_api_gateway_rest_api.api.root_resource_id
    execution_arn    = aws_api_gateway_rest_api.api.execution_arn
  }
}

output "api_gateway_stage" {
  description = "API Gateway stage information"
  value = {
    name         = aws_api_gateway_stage.api.stage_name
    invoke_url   = aws_api_gateway_stage.api.invoke_url
    deployment_id = aws_api_gateway_stage.api.deployment_id
  }
}

output "api_gateway_url" {
  description = "API Gateway invoke URL"
  value       = aws_api_gateway_stage.api.invoke_url
}

output "usage_plan" {
  description = "API Gateway usage plan"
  value = {
    id   = aws_api_gateway_usage_plan.api.id
    name = aws_api_gateway_usage_plan.api.name
  }
}

output "log_group" {
  description = "CloudWatch log group for API Gateway"
  value = {
    name = aws_cloudwatch_log_group.api_gateway.name
    arn  = aws_cloudwatch_log_group.api_gateway.arn
  }
}

output "api_key" {
  description = "API Gateway API key"
  value = {
    id    = aws_api_gateway_api_key.api_key.id
    name  = aws_api_gateway_api_key.api_key.name
    value = aws_api_gateway_api_key.api_key.value
  }
  sensitive = true
}
# Lambda Layers Module Outputs

output "common_layer" {
  description = "Common dependencies layer details"
  value = {
    arn     = aws_lambda_layer_version.common_dependencies.arn
    version = aws_lambda_layer_version.common_dependencies.version
    name    = aws_lambda_layer_version.common_dependencies.layer_name
  }
}

output "api_layer" {
  description = "API dependencies layer details" 
  value = {
    arn     = aws_lambda_layer_version.api_dependencies.arn
    version = aws_lambda_layer_version.api_dependencies.version
    name    = aws_lambda_layer_version.api_dependencies.layer_name
  }
}

output "business_layer" {
  description = "Business logic layer details"
  value = {
    arn     = aws_lambda_layer_version.business_logic.arn
    version = aws_lambda_layer_version.business_logic.version
    name    = aws_lambda_layer_version.business_logic.layer_name
  }
}

# Convenience outputs for Lambda function usage
output "api_lambda_layers" {
  description = "List of layer ARNs for API Lambda function"
  value = [
    aws_lambda_layer_version.common_dependencies.arn,
    aws_lambda_layer_version.api_dependencies.arn,
    aws_lambda_layer_version.business_logic.arn
  ]
}

output "processor_lambda_layers" {
  description = "List of layer ARNs for processor Lambda functions"
  value = [
    aws_lambda_layer_version.common_dependencies.arn,
    aws_lambda_layer_version.business_logic.arn
  ]
}
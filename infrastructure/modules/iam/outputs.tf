# IAM Module Outputs

output "lambda_role" {
  description = "Lambda execution role"
  value = {
    name = aws_iam_role.lambda_role.name
    arn  = aws_iam_role.lambda_role.arn
    id   = aws_iam_role.lambda_role.id
  }
}

output "api_gateway_cloudwatch_role" {
  description = "API Gateway CloudWatch role"
  value = {
    name = aws_iam_role.api_gateway_cloudwatch_role.name
    arn  = aws_iam_role.api_gateway_cloudwatch_role.arn
    id   = aws_iam_role.api_gateway_cloudwatch_role.id
  }
}

output "lambda_role_arn" {
  description = "Lambda execution role ARN"
  value       = aws_iam_role.lambda_role.arn
}

output "api_gateway_cloudwatch_role_arn" {
  description = "API Gateway CloudWatch role ARN"
  value       = aws_iam_role.api_gateway_cloudwatch_role.arn
}

output "policies" {
  description = "Created IAM policies"
  value = {
    dynamodb_policy   = aws_iam_policy.dynamodb_policy.arn
    s3_policy         = aws_iam_policy.s3_policy.arn
    sqs_policy        = aws_iam_policy.sqs_policy.arn
    cloudwatch_policy = aws_iam_policy.cloudwatch_policy.arn
  }
}
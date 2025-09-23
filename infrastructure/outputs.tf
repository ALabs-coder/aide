# Main Terraform Configuration Outputs

# API Gateway
output "api_gateway_url" {
  description = "API Gateway invoke URL"
  value       = module.api_gateway.api_gateway_url
}

output "api_gateway_details" {
  description = "Complete API Gateway details"
  value       = module.api_gateway.api_gateway
}

output "api_key" {
  description = "API Gateway API key"
  value       = module.api_gateway.api_key
  sensitive   = true
}

# Lambda Functions
output "lambda_functions" {
  description = "Lambda function details"
  value       = module.lambda.functions
}

# S3 Bucket
output "s3_bucket" {
  description = "S3 bucket details"
  value       = module.s3.bucket
}

# DynamoDB Tables
output "dynamodb_tables" {
  description = "DynamoDB table details"
  value = {
    jobs         = module.dynamodb.jobs_table
    transactions = module.dynamodb.transactions_table
    usage        = module.dynamodb.usage_table
  }
}

# SQS Queues
output "sqs_queues" {
  description = "SQS queue details"
  value = {
    processing = module.sqs.processing_queue
    dlq        = module.sqs.dlq
  }
}

# IAM Roles
output "iam_roles" {
  description = "IAM role details"
  value       = module.iam.lambda_role
}

# CloudWatch Log Groups
output "log_groups" {
  description = "CloudWatch log group names"
  value = {
    lambda_logs     = module.lambda.log_groups
    api_gateway_logs = module.api_gateway.log_group.name
  }
}

# Frontend/UI
output "frontend" {
  description = "Frontend deployment details"
  value = {
    website_url           = module.frontend.website_url
    cloudfront_domain     = module.frontend.cloudfront_domain_name
    s3_bucket_name        = module.frontend.bucket_name
    cloudfront_distribution_id = module.frontend.cloudfront_distribution_id
  }
}

# Deployment Information
output "deployment_info" {
  description = "Deployment configuration information"
  value = {
    project_name = var.project_name
    aws_region   = local.region
    account_id   = local.account_id
    name_prefix  = local.name_prefix
  }
}
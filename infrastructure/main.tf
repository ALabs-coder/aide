# PDF Extractor API Infrastructure
# Terraform configuration for AWS Lambda-based PDF processing API

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
  
  # Uncomment and configure for remote state
  # backend "s3" {
  #   bucket         = "your-terraform-state-bucket"
  #   key            = "pdf-extractor-api/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "terraform-state-lock"
  #   encrypt        = true
  # }
}

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project   = var.project_name
      ManagedBy = "Terraform"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Local values
locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  
  common_tags = {
    Project   = var.project_name
    ManagedBy = "Terraform"
  }
  
  # Simple resource naming - using 'dev' prefix for dev deployment
  name_prefix = "dev"
}

# DynamoDB Module - Created first as IAM needs the ARNs
module "dynamodb" {
  source = "./modules/dynamodb"
  
  name_prefix = local.name_prefix
  tags        = local.common_tags
}

# S3 Module - Created second as IAM needs the ARN
module "s3" {
  source = "./modules/s3"

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

# SQS Module - Created third as IAM needs the ARNs
module "sqs" {
  source = "./modules/sqs"

  name_prefix    = local.name_prefix
  tags           = local.common_tags
  s3_bucket_arn  = module.s3.bucket.arn

  depends_on = [module.s3]
}

# S3 Notification Configuration - REMOVED
# The Upload Lambda already triggers processing via SQS, so S3 notifications are redundant
# and were causing duplicate/malformed messages to be sent to the processing queue
#
# Previous configuration caused issues:
# - S3 ObjectCreated events → SQS (S3 event format - wrong format for processor)
# - Upload Lambda → SQS (correct job format)
#
# Now only Upload Lambda sends messages in the correct format
#
# resource "aws_s3_bucket_notification" "storage_notification" {
#   bucket = module.s3.bucket.id
#   queue {
#     queue_arn     = module.sqs.processing_queue.arn
#     events        = ["s3:ObjectCreated:*"]
#     filter_prefix = "uploads/"
#     filter_suffix = ".pdf"
#   }
#   depends_on = [module.s3, module.sqs]
# }

# IAM Module - Created fourth as it needs other modules' ARNs
module "iam" {
  source = "./modules/iam"

  name_prefix = local.name_prefix
  aws_region  = var.aws_region
  account_id  = local.account_id
  tags        = local.common_tags

  # Dependencies from other modules
  dynamodb_table_arns = module.dynamodb.table_arns
  s3_bucket_arn       = module.s3.bucket.arn
  sqs_queue_arns      = module.sqs.queue_arns

  depends_on = [module.dynamodb, module.s3, module.sqs]
}


# Lambda Layers Module - Must be created before Lambda functions
module "lambda_layers" {
  source = "./modules/lambda_layers"
  
  name_prefix = local.name_prefix
  tags        = local.common_tags
  layers_dir  = "lambda_packages/layers"
}

# Lambda Module - Now uses layers for dependencies
module "lambda" {
  source = "./modules/lambda"
  
  name_prefix  = local.name_prefix
  tags         = local.common_tags
  functions_dir = "lambda_packages/functions"
  
  # Dependencies from other modules
  lambda_role_arn      = module.iam.lambda_role.arn
  processing_queue_arn = module.sqs.processing_queue.arn
  dlq_arn              = module.sqs.dlq.arn
  
  # Lambda layers from layers module
  api_lambda_layers       = module.lambda_layers.api_lambda_layers
  processor_lambda_layers = module.lambda_layers.processor_lambda_layers
  
  # Environment variables for all functions
  environment_variables = {
    JOBS_TABLE_NAME              = module.dynamodb.jobs_table.name
    TRANSACTIONS_TABLE           = module.dynamodb.transactions_table.name
    USAGE_TABLE_NAME             = module.dynamodb.usage_table.name
    BANK_CONFIGURATIONS_TABLE    = module.dynamodb.bank_configurations_table.name
    S3_BUCKET_NAME               = module.s3.bucket.id
    PROCESSING_QUEUE_URL         = module.sqs.processing_queue.url
    DLQ_URL                      = module.sqs.dlq.url
  }

  depends_on = [module.iam, module.s3, module.sqs, module.lambda_layers]
}

# API Gateway Module
module "api_gateway" {
  source = "./modules/api_gateway"

  name_prefix           = local.name_prefix
  tags                  = local.common_tags

  # Dependencies from Lambda module
  lambda_invoke_arn               = module.lambda.functions.api.invoke_arn
  lambda_function_name            = module.lambda.functions.api.name
  upload_lambda_invoke_arn        = module.lambda.functions.upload.invoke_arn
  upload_lambda_function_name     = module.lambda.functions.upload.name
  statement_data_lambda_invoke_arn = module.lambda.functions.statement_data.invoke_arn
  statement_data_lambda_name       = module.lambda.functions.statement_data.name
  excel_export_lambda_invoke_arn   = module.lambda.functions.excel_export.invoke_arn
  excel_export_lambda_name         = module.lambda.functions.excel_export.name
  pdf_viewer_lambda_invoke_arn     = module.lambda.functions.pdf_viewer.invoke_arn
  pdf_viewer_lambda_name           = module.lambda.functions.pdf_viewer.name

  depends_on = [module.lambda, module.iam]
}

# Frontend Module (UI hosting with CloudFront)
module "frontend" {
  source = "./modules/frontend"

  name_prefix     = local.name_prefix
  bucket_name     = "pdf-extractor-ui-static"
  ui_build_path   = "../ui/dist"

  # API configuration for secure frontend build
  api_gateway_url = module.api_gateway.api_gateway_url
  api_key         = module.api_gateway.api_key.value

  # Content Security Policy
  csp_policy = "default-src * 'unsafe-inline' 'unsafe-eval' data: blob:;"

  tags = local.common_tags

  depends_on = [module.api_gateway]
}
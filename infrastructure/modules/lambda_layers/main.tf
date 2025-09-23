# Lambda Layers for PDF Extractor API
# Creates reusable layers for shared dependencies

# Common Dependencies Layer
resource "aws_lambda_layer_version" "common_dependencies" {
  filename         = "${var.layers_dir}/pdf-extractor-common.zip"
  layer_name       = "${var.name_prefix}-common"
  source_code_hash = filebase64sha256("${var.layers_dir}/pdf-extractor-common.zip")

  compatible_runtimes = ["python3.11"]
  description         = "Common dependencies: boto3, pdfplumber, pandas, pydantic, etc."
}

# API Dependencies Layer  
resource "aws_lambda_layer_version" "api_dependencies" {
  filename         = "${var.layers_dir}/pdf-extractor-api.zip"
  layer_name       = "${var.name_prefix}-api"
  source_code_hash = filebase64sha256("${var.layers_dir}/pdf-extractor-api.zip")

  compatible_runtimes = ["python3.11"]
  description         = "API dependencies: FastAPI, uvicorn, mangum, httpx"
}

# Business Logic Layer
resource "aws_lambda_layer_version" "business_logic" {
  filename         = "${var.layers_dir}/pdf-extractor-business.zip"
  layer_name       = "${var.name_prefix}-business"
  source_code_hash = filebase64sha256("${var.layers_dir}/pdf-extractor-business.zip")

  compatible_runtimes = ["python3.11"]
  description         = "Business logic modules: auth, config, logging, PDF extraction"
}

# Layer permissions - allow Lambda functions to use these layers
resource "aws_lambda_layer_version_permission" "common_dependencies" {
  layer_name     = aws_lambda_layer_version.common_dependencies.layer_name
  version_number = aws_lambda_layer_version.common_dependencies.version
  statement_id   = "AllowLambdaUsage"
  action         = "lambda:GetLayerVersion"
  principal      = data.aws_caller_identity.current.account_id
}

resource "aws_lambda_layer_version_permission" "api_dependencies" {
  layer_name     = aws_lambda_layer_version.api_dependencies.layer_name
  version_number = aws_lambda_layer_version.api_dependencies.version
  statement_id   = "AllowLambdaUsage"
  action         = "lambda:GetLayerVersion"
  principal      = data.aws_caller_identity.current.account_id
}

resource "aws_lambda_layer_version_permission" "business_logic" {
  layer_name     = aws_lambda_layer_version.business_logic.layer_name
  version_number = aws_lambda_layer_version.business_logic.version
  statement_id   = "AllowLambdaUsage"
  action         = "lambda:GetLayerVersion"
  principal      = data.aws_caller_identity.current.account_id
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}
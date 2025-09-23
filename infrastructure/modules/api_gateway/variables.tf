# API Gateway Module Variables

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}


variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}

variable "lambda_invoke_arn" {
  description = "Lambda function invoke ARN"
  type        = string
}

variable "lambda_function_name" {
  description = "Lambda function name"
  type        = string
}

variable "upload_lambda_invoke_arn" {
  description = "Upload Lambda function invoke ARN"
  type        = string
}

variable "upload_lambda_function_name" {
  description = "Upload Lambda function name"
  type        = string
}

variable "statement_data_lambda_invoke_arn" {
  description = "Statement Data Lambda function invoke ARN"
  type        = string
}

variable "statement_data_lambda_name" {
  description = "Statement Data Lambda function name"
  type        = string
}

variable "pdf_viewer_lambda_invoke_arn" {
  description = "PDF Viewer Lambda function invoke ARN"
  type        = string
}

variable "pdf_viewer_lambda_name" {
  description = "PDF Viewer Lambda function name"
  type        = string
}

variable "excel_export_lambda_invoke_arn" {
  description = "Excel Export Lambda function invoke ARN"
  type        = string
}

variable "excel_export_lambda_name" {
  description = "Excel Export Lambda function name"
  type        = string
}

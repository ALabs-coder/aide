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
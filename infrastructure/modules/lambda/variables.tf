# Lambda Module Variables - Layer-based Architecture

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}

variable "functions_dir" {
  description = "Directory containing pre-built Lambda function packages"
  type        = string
}

variable "lambda_role_arn" {
  description = "Lambda execution role ARN"
  type        = string
}

variable "processing_queue_arn" {
  description = "Processing queue ARN"
  type        = string
}

variable "dlq_arn" {
  description = "Dead Letter Queue ARN"
  type        = string
}

# Lambda Layer configurations
variable "api_lambda_layers" {
  description = "List of layer ARNs for API Lambda function"
  type        = list(string)
}

variable "processor_lambda_layers" {
  description = "List of layer ARNs for processor Lambda functions"
  type        = list(string)
}

# Environment variables
variable "environment_variables" {
  description = "Environment variables for Lambda functions"
  type        = map(string)
  default     = {}
}

# Optional SNS topic for alerts
variable "alert_sns_topic_arn" {
  description = "SNS topic ARN for alerts (optional)"
  type        = string
  default     = ""
}
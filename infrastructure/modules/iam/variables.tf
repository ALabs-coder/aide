# IAM Module Variables

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "account_id" {
  description = "AWS account ID"
  type        = string
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}

variable "dynamodb_table_arns" {
  description = "List of DynamoDB table ARNs"
  type        = list(string)
}

variable "s3_bucket_arn" {
  description = "S3 bucket ARN"
  type        = string
}

variable "sqs_queue_arns" {
  description = "List of SQS queue ARNs"
  type        = list(string)
}
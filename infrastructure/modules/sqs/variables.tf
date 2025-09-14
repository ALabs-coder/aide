# SQS Module Variables

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}

variable "s3_bucket_arn" {
  description = "S3 bucket ARN for notifications"
  type        = string
}
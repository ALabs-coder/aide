# Backend Module Variables

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
  default     = {}
}
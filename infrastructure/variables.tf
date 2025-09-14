# Variables for PDF Extractor API

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "pdf-extractor-api"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}
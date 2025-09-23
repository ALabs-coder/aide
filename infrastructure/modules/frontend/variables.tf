# Variables for the frontend module

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "bucket_name" {
  description = "Name of the S3 bucket for UI hosting"
  type        = string
}

variable "ui_build_path" {
  description = "Path to the built UI files"
  type        = string
}

variable "csp_policy" {
  description = "Content Security Policy for the UI"
  type        = string
  default     = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' https:; media-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self';"
}

variable "api_gateway_url" {
  description = "API Gateway URL for the frontend"
  type        = string
}

variable "api_key" {
  description = "API key for the frontend"
  type        = string
  sensitive   = true
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
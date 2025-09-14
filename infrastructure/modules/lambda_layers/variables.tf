# Lambda Layers Module Variables

variable "name_prefix" {
  description = "Prefix for naming resources"
  type        = string
}

variable "layers_dir" {
  description = "Directory containing built layer zip files"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
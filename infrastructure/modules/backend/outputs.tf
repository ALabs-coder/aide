# Backend Module Outputs

output "state_bucket" {
  description = "S3 bucket for Terraform state"
  value = {
    name   = aws_s3_bucket.terraform_state.bucket
    arn    = aws_s3_bucket.terraform_state.arn
    region = aws_s3_bucket.terraform_state.region
  }
}

output "state_lock_table" {
  description = "DynamoDB table for state locking"
  value = {
    name = aws_dynamodb_table.terraform_state_lock.name
    arn  = aws_dynamodb_table.terraform_state_lock.arn
  }
}

output "backend_config" {
  description = "Backend configuration for use in terraform block"
  value = {
    bucket         = aws_s3_bucket.terraform_state.bucket
    key            = "pdf-extractor-api/terraform.tfstate"
    region         = var.aws_region
    dynamodb_table = aws_dynamodb_table.terraform_state_lock.name
    encrypt        = true
  }
}

output "backend_config_string" {
  description = "Formatted backend configuration string"
  value = <<-EOT
    terraform {
      backend "s3" {
        bucket         = "${aws_s3_bucket.terraform_state.bucket}"
        key            = "pdf-extractor-api/terraform.tfstate"
        region         = "${var.aws_region}"
        dynamodb_table = "${aws_dynamodb_table.terraform_state_lock.name}"
        encrypt        = true
      }
    }
  EOT
}
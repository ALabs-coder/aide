# S3 Module Outputs

output "bucket" {
  description = "S3 bucket information"
  value = {
    id     = aws_s3_bucket.storage.id
    arn    = aws_s3_bucket.storage.arn
    name   = aws_s3_bucket.storage.bucket
    domain = aws_s3_bucket.storage.bucket_domain_name
    region = aws_s3_bucket.storage.region
  }
}

output "bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.storage.bucket
}

output "bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.storage.arn
}

output "bucket_domain_name" {
  description = "S3 bucket domain name"
  value       = aws_s3_bucket.storage.bucket_domain_name
}
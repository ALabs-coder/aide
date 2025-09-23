# Outputs for the frontend module

output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.ui_bucket.bucket
}

output "bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.ui_bucket.arn
}

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.ui_distribution.id
}

output "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.ui_distribution.arn
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.ui_distribution.domain_name
}

output "cloudfront_hosted_zone_id" {
  description = "Hosted zone ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.ui_distribution.hosted_zone_id
}

output "website_url" {
  description = "URL of the website"
  value       = "https://${aws_cloudfront_distribution.ui_distribution.domain_name}"
}
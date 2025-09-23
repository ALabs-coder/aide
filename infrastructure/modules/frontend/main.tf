# Frontend Infrastructure for PDF Extractor UI
# S3 bucket for static website hosting and CloudFront distribution

# S3 bucket for hosting the UI
resource "aws_s3_bucket" "ui_bucket" {
  bucket = var.bucket_name

  tags = var.tags
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "ui_bucket_versioning" {
  bucket = aws_s3_bucket.ui_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "ui_bucket_encryption" {
  bucket = aws_s3_bucket.ui_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block all public access to the bucket (CloudFront will access via OAC)
resource "aws_s3_bucket_public_access_block" "ui_bucket_pab" {
  bucket = aws_s3_bucket.ui_bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Origin Access Control for CloudFront
resource "aws_cloudfront_origin_access_control" "ui_oac" {
  name                              = "${var.name_prefix}-ui-oac"
  description                       = "Origin Access Control for PDF Extractor UI"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront distribution
resource "aws_cloudfront_distribution" "ui_distribution" {
  origin {
    domain_name              = aws_s3_bucket.ui_bucket.bucket_regional_domain_name
    origin_access_control_id = aws_cloudfront_origin_access_control.ui_oac.id
    origin_id                = "S3-${aws_s3_bucket.ui_bucket.bucket}"
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "PDF Extractor UI Distribution"
  default_root_object = "index.html"

  # Cache behavior for the UI
  default_cache_behavior {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.ui_bucket.bucket}"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400

    # Security headers
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id
  }

  # Cache behavior for assets (longer TTL)
  ordered_cache_behavior {
    path_pattern     = "/assets/*"
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.ui_bucket.bucket}"

    forwarded_values {
      query_string = false
      headers      = ["Origin"]
      cookies {
        forward = "none"
      }
    }

    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000
    compress               = true
    viewer_protocol_policy = "redirect-to-https"
  }

  # Error pages
  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = var.tags
}

# Security Headers Policy
resource "aws_cloudfront_response_headers_policy" "security_headers" {
  name    = "${var.name_prefix}-ui-security-headers"
  comment = "Security headers for PDF Extractor UI"

  cors_config {
    access_control_allow_credentials = false

    access_control_allow_headers {
      items = ["*"]
    }

    access_control_allow_methods {
      items = ["ALL"]
    }

    access_control_allow_origins {
      items = ["*"]
    }

    origin_override = true
  }

  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      override                   = true
    }

    content_type_options {
      override = true
    }

    frame_options {
      frame_option = "DENY"
      override     = true
    }

    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }

    content_security_policy {
      content_security_policy = var.csp_policy
      override                = true
    }
  }
}

# Bucket policy to allow CloudFront access
resource "aws_s3_bucket_policy" "ui_bucket_policy" {
  bucket = aws_s3_bucket.ui_bucket.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontServicePrincipal"
        Effect    = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.ui_bucket.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.ui_distribution.arn
          }
        }
      }
    ]
  })
}

# Build the frontend with proper environment variables
resource "null_resource" "build_frontend" {
  # Trigger rebuild when API configuration changes
  triggers = {
    api_gateway_url = var.api_gateway_url
    api_key_hash    = sha256(var.api_key)
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ../ui
      echo "VITE_API_BASE_URL=${var.api_gateway_url}" > .env.local
      echo "VITE_API_KEY=${var.api_key}" >> .env.local
      npm run build
    EOT
  }
}

# Upload UI files to S3
resource "aws_s3_object" "ui_files" {
  for_each = fileset(var.ui_build_path, "**/*")

  bucket = aws_s3_bucket.ui_bucket.id
  key    = each.value
  source = "${var.ui_build_path}/${each.value}"

  # Depend on the build process
  depends_on = [null_resource.build_frontend]

  # Set content type based on file extension
  content_type = lookup({
    "html" = "text/html"
    "css"  = "text/css"
    "js"   = "application/javascript"
    "json" = "application/json"
    "png"  = "image/png"
    "jpg"  = "image/jpeg"
    "jpeg" = "image/jpeg"
    "gif"  = "image/gif"
    "svg"  = "image/svg+xml"
    "ico"  = "image/x-icon"
    "woff" = "font/woff"
    "woff2" = "font/woff2"
    "ttf"  = "font/ttf"
    "eot"  = "application/vnd.ms-fontobject"
  }, split(".", each.value)[length(split(".", each.value)) - 1], "application/octet-stream")

  # Generate etag for cache invalidation
  etag = filemd5("${var.ui_build_path}/${each.value}")

  tags = var.tags
}
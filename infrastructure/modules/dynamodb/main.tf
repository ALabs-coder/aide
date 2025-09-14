# DynamoDB Tables for PDF Extractor API

# Jobs table - tracks PDF processing jobs
resource "aws_dynamodb_table" "jobs" {
  name           = "${var.name_prefix}-jobs"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "job_id"
  
  attribute {
    name = "job_id"
    type = "S"
  }
  
  attribute {
    name = "user_id"
    type = "S"
  }
  
  attribute {
    name = "status"
    type = "S"
  }
  
  attribute {
    name = "created_at"
    type = "S"
  }

  # GSI for querying jobs by user_id
  global_secondary_index {
    name     = "user-jobs-index"
    hash_key = "user_id"
    range_key = "created_at"
    projection_type = "ALL"
  }

  # GSI for querying jobs by status
  global_secondary_index {
    name     = "status-index"
    hash_key = "status"
    range_key = "created_at"
    projection_type = "ALL"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # TTL for automatic cleanup of old records (30 days)
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-jobs"
    Type = "DynamoDB"
  })
}

# Transactions table - tracks API usage and billing
resource "aws_dynamodb_table" "transactions" {
  name           = "${var.name_prefix}-transactions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "transaction_id"
  
  attribute {
    name = "transaction_id"
    type = "S"
  }
  
  attribute {
    name = "user_id"
    type = "S"
  }
  
  attribute {
    name = "created_at"
    type = "S"
  }

  # GSI for querying transactions by user_id
  global_secondary_index {
    name     = "user-transactions-index"
    hash_key = "user_id"
    range_key = "created_at"
    projection_type = "ALL"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # TTL for automatic cleanup of old records (90 days for billing)
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-transactions"
    Type = "DynamoDB"
  })
}

# Usage table - tracks rate limiting and quotas
resource "aws_dynamodb_table" "usage" {
  name           = "${var.name_prefix}-usage"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  range_key      = "time_window"
  
  attribute {
    name = "user_id"
    type = "S"
  }
  
  attribute {
    name = "time_window"
    type = "S"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # TTL for automatic cleanup (24 hours)
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-usage"
    Type = "DynamoDB"
  })
}
# SQS Queues for PDF Processing

# Dead Letter Queue for failed messages
resource "aws_sqs_queue" "dlq" {
  name = "${var.name_prefix}-dlq"

  # Visibility timeout should be at least 6x the Lambda timeout (300s * 6 = 1800s)
  visibility_timeout_seconds = 1800

  # Message retention period (14 days)
  message_retention_seconds = 1209600

  # Enable server-side encryption
  sqs_managed_sse_enabled = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-dlq"
    Type = "SQS-DLQ"
  })
}

# Main processing queue
resource "aws_sqs_queue" "processing" {
  name = "${var.name_prefix}-processing"

  # Visibility timeout should be longer than Lambda timeout
  visibility_timeout_seconds = 720

  # Message retention period (7 days)
  message_retention_seconds = 604800

  # Enable server-side encryption
  sqs_managed_sse_enabled = true

  # Configure dead letter queue
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = 2
  })

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-processing"
    Type = "SQS"
  })
}

# SQS Policy - REMOVED S3 permissions
# S3 bucket notifications have been removed, so S3 no longer needs
# permission to send messages to the SQS queue.
# Only Lambda functions now send messages via IAM roles.
#
# Previous configuration:
# - Allowed S3 service to send messages when objects are created
# - This was causing duplicate messages with wrong format
#
# Now only Lambda functions send messages via their IAM roles
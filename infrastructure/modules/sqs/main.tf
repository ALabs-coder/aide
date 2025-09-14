# SQS Queues for PDF Processing

# Dead Letter Queue for failed messages
resource "aws_sqs_queue" "dlq" {
  name = "${var.name_prefix}-dlq"

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

# Allow S3 to send messages to the processing queue
data "aws_iam_policy_document" "sqs_policy" {
  statement {
    sid    = "AllowS3Publish"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["s3.amazonaws.com"]
    }

    actions = [
      "sqs:SendMessage"
    ]

    resources = [
      aws_sqs_queue.processing.arn
    ]

    condition {
      test     = "ArnEquals"
      variable = "aws:SourceArn"
      values   = [var.s3_bucket_arn]
    }
  }
}

# Apply the policy to the processing queue
resource "aws_sqs_queue_policy" "processing" {
  queue_url = aws_sqs_queue.processing.id
  policy    = data.aws_iam_policy_document.sqs_policy.json
}
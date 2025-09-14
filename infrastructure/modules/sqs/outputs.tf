# SQS Module Outputs

output "processing_queue" {
  description = "Processing SQS queue information"
  value = {
    id   = aws_sqs_queue.processing.id
    arn  = aws_sqs_queue.processing.arn
    name = aws_sqs_queue.processing.name
    url  = aws_sqs_queue.processing.url
  }
}

output "dlq" {
  description = "Dead Letter Queue information"
  value = {
    id   = aws_sqs_queue.dlq.id
    arn  = aws_sqs_queue.dlq.arn
    name = aws_sqs_queue.dlq.name
    url  = aws_sqs_queue.dlq.url
  }
}

output "queue_arns" {
  description = "List of all SQS queue ARNs"
  value = [
    aws_sqs_queue.processing.arn,
    aws_sqs_queue.dlq.arn,
  ]
}

output "queue_urls" {
  description = "Map of queue URLs"
  value = {
    processing = aws_sqs_queue.processing.url
    dlq        = aws_sqs_queue.dlq.url
  }
}
# DynamoDB Module Outputs

output "jobs_table" {
  description = "DynamoDB jobs table"
  value = {
    name = aws_dynamodb_table.jobs.name
    arn  = aws_dynamodb_table.jobs.arn
    id   = aws_dynamodb_table.jobs.id
  }
}

output "transactions_table" {
  description = "DynamoDB transactions table"
  value = {
    name = aws_dynamodb_table.transactions.name
    arn  = aws_dynamodb_table.transactions.arn
    id   = aws_dynamodb_table.transactions.id
  }
}

output "usage_table" {
  description = "DynamoDB usage table"
  value = {
    name = aws_dynamodb_table.usage.name
    arn  = aws_dynamodb_table.usage.arn
    id   = aws_dynamodb_table.usage.id
  }
}

output "table_arns" {
  description = "List of all DynamoDB table ARNs"
  value = [
    aws_dynamodb_table.jobs.arn,
    aws_dynamodb_table.transactions.arn,
    aws_dynamodb_table.usage.arn,
  ]
}

output "table_names" {
  description = "Map of table names"
  value = {
    jobs         = aws_dynamodb_table.jobs.name
    transactions = aws_dynamodb_table.transactions.name
    usage        = aws_dynamodb_table.usage.name
  }
}
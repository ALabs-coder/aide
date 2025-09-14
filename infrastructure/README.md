# PDF Extractor API Infrastructure

Simple Terraform infrastructure for the PDF Extractor API.

## Quick Start

1. **Initialize Terraform:**
   ```bash
   terraform init
   ```

2. **Plan the deployment:**
   ```bash
   terraform plan
   ```

3. **Deploy the infrastructure:**
   ```bash
   terraform apply
   ```

4. **Get the API URL:**
   ```bash
   terraform output api_gateway_url
   ```

## What Gets Created

- **API Gateway**: REST API with CORS support
- **Lambda Functions**: 4 functions (api, processor, cleanup, dlq-processor)  
- **DynamoDB Tables**: 3 tables (jobs, transactions, usage)
- **S3 Bucket**: File storage with lifecycle policies
- **SQS Queues**: Processing queue and dead letter queue
- **IAM Roles**: Proper permissions for all services

## Configuration

The infrastructure uses sensible defaults. You can customize by editing `terraform.tfvars`:

```hcl
project_name = "pdf-extractor-api"
aws_region   = "us-east-1"
```

## Clean Up

To destroy the infrastructure:

```bash
terraform destroy
```
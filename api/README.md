# PDF Bank Statement Processing API

A FastAPI-based system for uploading PDF bank statements to S3, storing metadata in DynamoDB, and extracting transaction data.

## Features

- **S3 Upload**: Store PDF files in AWS S3 with organized folder structure
- **DynamoDB Storage**: Track file metadata with 60-day TTL
- **PDF Extraction**: Extract transaction data from bank statements  
- **Multiple Formats**: Return data as JSON or CSV
- **Lifecycle Management**: Automatic cleanup (PDFs: 7 days, Results: 14 days)

## Quick Start

### AWS Deployment
```bash
# Setup
npm install -g serverless
aws configure

# Deploy Infrastructure + Functions
cd api
npm install
serverless deploy --stage dev

# Code-only updates (after initial deploy)
serverless deploy function --function api --stage dev
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check |
| `/upload` | POST | Upload PDF to S3 + DynamoDB |
| `/extract` | POST | Extract data from PDF |
| `/docs` | GET | Interactive API docs |

### Upload to S3
```bash
curl -X POST "https://your-api-gateway-url/upload" \
  -F "file=@statement.pdf" \
  -F "X-API-KEY=your-api-key"
```

### Extract Data
```bash
curl -X POST "https://your-api-gateway-url/extract" \
  -F "file=@statement.pdf" \
  -F "X-API-KEY=your-api-key"
```

## AWS Resources Created

### DynamoDB Tables
- `pdf-extractor-api-dev-jobs` - File metadata (60-day TTL)
- `pdf-extractor-api-dev-transactions` - Extracted data
- `pdf-extractor-api-dev-usage` - Usage tracking

### S3 Bucket Structure
```
pdf-extractor-api-dev-storage/
├── uploads/2025/01/13/uuid_filename.pdf    (7-day lifecycle)
├── results/processed_data.json             (14-day lifecycle)  
└── temp/processing_files                   (1-day lifecycle)
```

### Lambda Functions
- `pdf-extractor-api-dev-api` - Main API
- `pdf-extractor-api-dev-processor` - Async processing
- `pdf-extractor-api-dev-cleanup` - Scheduled cleanup

## Data Lifecycle

| Resource | Retention | Auto-Delete |
|----------|-----------|-------------|
| PDF Files | 7 days | S3 Lifecycle |
| Database Records | 60 days | DynamoDB TTL |
| Processing Results | 14 days | S3 Lifecycle |
| Temp Files | 1 day | S3 Lifecycle |

## Configuration

### Environment Variables
```bash
# AWS Configuration
AWS_REGION=us-east-1
STAGE=dev

# API Keys (handled by AWS API Gateway)
# No API key environment variables needed - authentication handled by API Gateway
```

### Frontend Integration
```javascript
const handleFileUpload = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('X-API-KEY', 'your-api-key');

  const response = await fetch('https://your-api-gateway-url/upload', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  console.log('Job ID:', result.job_id);
  console.log('S3 Key:', result.s3_key);
};
```

## Development Commands

```bash
# Deploy to AWS
serverless deploy --stage dev

# Function-only deploy (faster)
serverless deploy function --function api --stage dev

# Remove AWS resources
serverless remove --stage dev

# View logs
serverless logs --function api --stage dev --tail
```

## Project Structure

```
api/
├── main.py                     # FastAPI app
├── serverless.yml              # AWS infrastructure config
├── lambda_handler.py           # AWS Lambda entry point
├── extract_pdf_to_csv.py       # PDF processing logic
└── requirements.txt            # Python dependencies

ui/
├── src/
│   ├── App.tsx                 # Main React app
│   └── components/
│       └── FileUploadModal.tsx # File upload UI
└── package.json
```

## Troubleshooting

### AWS Deployment Issues
```bash
# Check AWS credentials
aws sts get-caller-identity

# View CloudFormation stack
aws cloudformation describe-stacks --stack-name pdf-extractor-api-dev

# Check DynamoDB tables
aws dynamodb list-tables

# Check S3 bucket
aws s3 ls pdf-extractor-api-dev-storage
```

## Security Notes

- ✅ Protected resources with `DeletionPolicy: Retain`
- ✅ API key authentication required
- ✅ CORS configured for frontend domains  
- ✅ Automatic data cleanup via TTL/lifecycle rules
- ⚠️ Use secure API keys in real deployments
- ⚠️ Configure proper IAM roles for your AWS account

---

**Quick Access:**
- AWS Console: Search for "pdf-extractor-api-dev"
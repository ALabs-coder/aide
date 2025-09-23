# PDF Bank Statement Extractor

A modern, serverless PDF processing application that extracts and structures transaction data from bank statements using AI/ML techniques.

## 🏗️ Architecture

```
├── api/                    # Python Lambda functions & business logic
│   ├── lambda_handler.py   # Main API entry point
│   ├── main.py            # Core processing logic
│   ├── auth.py            # Authentication & authorization
│   ├── extract_pdf_to_csv.py # PDF processing utilities
│   └── ...
├── ui/                     # Next.js frontend application
│   ├── src/               # React components & pages
│   └── ...
├── infrastructure/         # Terraform infrastructure as code
│   ├── *.tf               # AWS resource definitions
│   ├── deploy-terraform.sh # Deployment automation
│   └── setup-s3-backend.sh # Remote state setup
└── app/                   # Additional application components
```

## 🚀 Quick Start

### Prerequisites
- **Terraform** >= 1.0
- **AWS CLI** configured with appropriate credentials
- **Node.js** >= 18 (for UI development)
- **Python** 3.11 (for API development)
- **jq** (for deployment scripts)

### 1. Infrastructure Deployment

```bash
# Navigate to infrastructure directory
cd infrastructure

# Set up S3 remote state (one-time setup)
./setup-s3-backend.sh

# Deploy infrastructure
./deploy-terraform.sh dev us-east-1 infrastructure

# For subsequent code updates (faster)
./deploy-terraform.sh dev us-east-1 code
```

### 2. Frontend Development

```bash
cd ui
npm install
npm run dev
```


## 🛠️ Development Workflow

### Infrastructure Changes
```bash
cd infrastructure
./deploy-terraform.sh dev infrastructure  # Full deployment
```

### Code Changes Only
```bash
cd infrastructure
./deploy-terraform.sh dev code  # Fast Lambda-only deployment
```

### Environment Variables
```bash
# Set before deployment
export TF_VAR_valid_api_keys="your-api-key-1,your-api-key-2"
export TF_VAR_jwt_secret_key="your-jwt-secret-key"
```

## 📁 Component Overview

### API (`/api/`)
- **Serverless Python functions** running on AWS Lambda
- **FastAPI-based** REST API with automatic documentation
- **JWT & API key authentication**
- **PDF processing** with OCR and data extraction
- **DynamoDB integration** for data persistence
- **S3 integration** for file storage

### UI (`/ui/`)  
- **Next.js** React application
- **Tailwind CSS** for styling
- **TypeScript** for type safety
- **File upload interface**
- **Real-time processing status**
- **Results visualization**

### Infrastructure (`/infrastructure/`)
- **Terraform** infrastructure as code
- **S3 remote state** for team collaboration
- **AWS Lambda functions** (4 functions)
- **DynamoDB tables** (3 tables) with data preservation
- **S3 storage** with lifecycle policies
- **API Gateway** with CORS support
- **SQS queues** for async processing
- **CloudWatch** logging and monitoring

## 🔐 Security Features

- **IAM least privilege** access controls
- **Encryption at rest** (S3, DynamoDB)
- **API authentication** (JWT + API keys)
- **CORS configuration** for secure frontend access
- **VPC support** (optional, for enhanced security)
- **No hardcoded secrets** in configuration

## 💰 Cost Optimization

- **Pay-per-use** billing model (Lambda, DynamoDB, API Gateway)
- **Automatic cleanup** via S3 lifecycle policies
- **Reserved concurrency** limits to prevent cost spikes
- **Optimized memory allocation** for Lambda functions
- **Log retention policies** for storage cost management

## 🔄 Continuous Deployment

### Data Preservation Strategy
✅ **DynamoDB tables** - Data persists across deployments  
✅ **S3 storage** - Files managed by lifecycle policies  
✅ **Lambda functions** - Code updates only, no data loss  

### Deployment Types
- **Infrastructure** (`infrastructure`): Full AWS resource updates
- **Code** (`code`): Lambda function updates only (fastest)

### Team Collaboration
- **Remote state** in S3 with DynamoDB locking
- **State versioning** for rollback capability
- **Concurrent deployment protection**

## 📊 Monitoring & Observability

- **CloudWatch Logs** - Structured application logging
- **API Gateway Logs** - Request/response monitoring  
- **DynamoDB Streams** - Real-time data change events
- **SQS Monitoring** - Queue depth and processing metrics
- **Lambda Metrics** - Performance and error tracking

## 🧪 Testing

```bash
# API Tests
cd api
python -m pytest tests/

# Infrastructure Validation
cd infrastructure
terraform validate
terraform plan

# UI Tests
cd ui
npm test
```

## 🚨 Troubleshooting

### Common Issues

**Lambda deployment fails:**
```bash
cd infrastructure
rm lambda_function.zip
./deploy-terraform.sh dev code
```

**API Gateway 5xx errors:**
```bash
aws logs tail /aws/lambda/pdf-extractor-api-dev-api --follow
```

**State locking issues:**
```bash
# Force unlock (use carefully)
terraform force-unlock <lock-id>
```

## 📖 Additional Documentation

- [Infrastructure Setup Guide](infrastructure/README.md)
- [API Documentation](api/README.md) 
- [UI Development Guide](ui/README.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
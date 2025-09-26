## MANDATORY to follow these rules
  - First think through the problem, read the code base for relevant files, and write a plan to tasks/todo.md.
  - The plan should have a list of to-do items that you can check off as you complete them.
  - Before you begin working check in with me and I will verify the plan then begin working on the todo items, marking them as complete as you go 
  - Please every step of the way just give me a high-level explanation of what changes you made
  - Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes every change should impact as little code as possible. Everything is about simplicity 
  - Finally add a review section to the to do that MD file with a summary of the changes you made and any other relevant information. 
  - DO NOT BE LAZY, NEVER BE LAZY, IF THERE IS A BUG, FIND ROOT CAUSE AND FIX IT NO TEMPORARY FIXES YOU ARE A SENIOR DEVELOPER. NEVER BE LAZY 
  - MAKE ALL FIXES AND CODE CHANGES AS SIMPLE AS HUMANLY POSSIBLE. THEY SHOULD ONLY IMPACT NECESSARY CODE RELEVANT TO THE TASK AND NOTHING ELSE. IT SHOULD IMPACT AS LITTLE CODE AS POSSIBLE. YOUR GOAL IS TO NOT INTRODUCE ANY BUGS. IT IS ALL ABOUT SIMPLICITY

## Development Commands

### Frontend (UI)
```bash
cd ui
npm install                # Install dependencies
npm run dev               # Start development server
npm run build             # Build for production
npm run lint              # Run ESLint
npm run preview           # Preview production build
npm test                  # Run Playwright tests
```

### API Development
```bash
cd api
pip install -r requirements.txt  # Install Python dependencies
python -m pytest tests/         # Run API tests
```

### Infrastructure & Deployment
```bash
cd infrastructure

# Full infrastructure deployment
./scripts/build-all.sh          # Build Lambda layers and functions
terraform init                  # Initialize Terraform
terraform plan                  # Preview changes
terraform apply                 # Deploy infrastructure

# Code-only deployment (faster)
./scripts/build-functions.sh    # Build Lambda functions only
terraform apply                 # Deploy function updates only

# Individual build commands
./scripts/build-layers.sh       # Build Lambda layers only
./scripts/build-functions.sh    # Build Lambda functions only
```

## Architecture Overview

### Three-Tier Serverless Architecture
- **Frontend**: React/Vite application (`ui/`) with Tailwind CSS and TypeScript
- **API**: Python FastAPI serverless functions (`api/`) running on AWS Lambda
- **Infrastructure**: Terraform-managed AWS resources (`infrastructure/`)

### Key Components
- **Lambda Functions**: 4 functions (api, processor, cleanup, dlq_processor)
- **Lambda Layers**: 3 layers for optimized dependency management (80% storage reduction)
- **Data Storage**: DynamoDB tables (jobs, transactions, usage) + S3 bucket
- **Processing**: SQS queues for async PDF processing with DLQ for failed jobs
- **Authentication**: JWT + API key based authentication system

### Project Structure
```
├── api/                    # Python Lambda functions & business logic
│   ├── lambdas/           # Individual Lambda function handlers
│   ├── auth.py            # Authentication & authorization
│   ├── config.py          # Configuration management
│   └── extract_pdf_data.py # Core PDF processing logic
├── ui/                    # React/Vite frontend application
│   └── src/               # React components, pages, and utilities
├── infrastructure/        # Terraform infrastructure as code
│   ├── modules/           # Reusable Terraform modules
│   ├── scripts/           # Build and deployment scripts
│   └── *.tf               # AWS resource definitions
└── tests/                 # End-to-end tests
```

## Critical Development Guidelines

### AWS Infrastructure Changes
- **ALWAYS use Terraform** for AWS service changes
- Debug sessions can use AWS CLI commands to inspect resources
- Never make direct AWS console changes that bypass Terraform state

### Layer-Based Lambda Architecture
- Lambda functions are lightweight (1-3KB) and depend on shared layers
- Layers contain dependencies and shared business logic
- Always rebuild layers after dependency changes: `./scripts/build-layers.sh`
- Deploy both layers and functions after significant changes: `./scripts/build-all.sh`

### Environment Variables & Configuration

#### Local Development Setup
1. **Create local configuration** (first-time setup):
   ```bash
   cd infrastructure
   cp terraform.tfvars.example local.tfvars  # Create your local copy
   # Edit local.tfvars with your actual values
   ```

2. **Use local configuration**:
   ```bash
   # For all terraform commands in local development
   terraform plan -var-file="local.tfvars"
   terraform apply -var-file="local.tfvars"
   ```

#### Alternative: Environment Variables (Legacy Method)
```bash
export TF_VAR_environment="dev"
export TF_VAR_aws_region="us-east-1"
export TF_VAR_project_name="pdf-extractor-api"
export TF_VAR_api_gateway_stage="v1"
```

#### Configuration Files Structure
- `terraform.tfvars` - Template with placeholders for deployment (checked into git)
- `terraform.tfvars.example` - Example template for local development (checked into git)
- `local.tfvars` - Your actual local values (never commit - gitignored)

### Data Persistence Strategy
- **DynamoDB tables**: Data persists across deployments
- **S3 storage**: Files managed by lifecycle policies
- **Lambda functions**: Code updates only, no data loss

### Testing Strategy
- **API Tests**: `python -m pytest tests/` in the `api/` directory
- **Infrastructure Validation**: `terraform validate && terraform plan`
- **UI Tests**: `npm test` (Playwright) in the `ui/` directory

## Common Development Workflows

### Making Infrastructure Changes
1. Edit Terraform files in `infrastructure/`
2. Run `terraform plan` to preview changes
3. Run `terraform apply` to deploy changes

### Updating Lambda Function Code
1. Edit handler files in `api/lambdas/`
2. Run `./scripts/build-functions.sh`
3. Run `terraform apply`

### Updating Dependencies or Business Logic
1. Edit requirements files or business logic in `api/`
2. Run `./scripts/build-all.sh` (rebuilds both layers and functions)
3. Run `terraform apply`

### Deployment Types
- **Infrastructure deployment**: Use when changing AWS resources
- **Code deployment**: Use when updating Lambda function code only (faster)

#
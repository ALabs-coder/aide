# Terraform Variables with Placeholders
# These placeholders get replaced during deployment

# Project Configuration
project_name = "{{PROJECT_NAME}}"
aws_region   = "{{AWS_REGION}}"

# Environment-specific settings
environment = "{{ENVIRONMENT}}"
api_gateway_stage = "{{API_GATEWAY_STAGE}}"
# Bank Configurations API Endpoint

## Overview
This document describes the `/configurations/banks` API endpoint that provides active bank configurations for the frontend application.

## Endpoint Details

**URL**: `GET /configurations/banks`
**Authentication**: API Key required (`X-API-Key` header)
**Content-Type**: `application/json`

## Response Format

### Success Response (HTTP 200)
```json
{
  "status": "success",
  "data": [
    {
      "id": "CANARA",
      "name": "Canara Bank"
    },
    {
      "id": "UNION",
      "name": "Union Bank of India"
    }
  ],
  "count": 2
}
```

### Error Response (HTTP 500)
```json
{
  "status": "error",
  "error": "Internal Server Error",
  "message": "Failed to retrieve bank configurations",
  "data": [],
  "count": 0
}
```

## Features

- **Active Banks Only**: Returns only banks with `Status = 'ACTIVE'` from DynamoDB
- **Alphabetical Sorting**: Results are pre-sorted by bank name
- **Minimal Payload**: Only essential fields (`id`, `name`) for optimal performance
- **CORS Support**: Full CORS configuration for web applications
- **Error Handling**: Comprehensive error handling with detailed logging

## Implementation Details

### Database Schema
- **Table**: `dev-bank-configurations`
- **Partition Key**: `PK = 'BANK_CONFIG'`
- **Sort Key**: `SK = '{Status}#{Priority}#{BankCode}'`
- **Filter**: `Status = 'ACTIVE'`

### Infrastructure Components
- **API Gateway Resource**: `/configurations/banks`
- **Lambda Function**: `dev-api` (shared handler)
- **HTTP Methods**: `GET`, `OPTIONS` (CORS)
- **Authentication**: API Gateway API Key

### Frontend Integration
- **API Service**: `apiService.getBankConfigurations()`
- **TypeScript Interface**: `BankConfiguration`, `BankConfigurationsResponse`
- **Endpoint Configuration**: `API_ENDPOINTS.configurationsBank`

## Usage Example

```javascript
// Frontend usage
import { apiService } from '../services/api'

try {
  const response = await apiService.getBankConfigurations()
  console.log('Active banks:', response.data)
  // Output: [{ id: "CANARA", name: "Canara Bank" }, ...]
} catch (error) {
  console.error('Failed to fetch bank configurations:', error)
}
```

## Testing

```bash
# Test the endpoint
curl -X GET 'https://cypom236ui.execute-api.us-east-1.amazonaws.com/dev/configurations/banks' \
  -H 'X-API-Key: YOUR_API_KEY' \
  -H 'Content-Type: application/json'

# Test CORS preflight
curl -X OPTIONS 'https://cypom236ui.execute-api.us-east-1.amazonaws.com/dev/configurations/banks' \
  -H 'Origin: http://localhost:5173' \
  -H 'Access-Control-Request-Method: GET' \
  -H 'Access-Control-Request-Headers: X-API-Key'
```

## Deployment

After making changes to the Lambda handler or API Gateway configuration:

1. Build Lambda functions: `./scripts/build-functions.sh`
2. Deploy infrastructure: `terraform apply`

The endpoint follows the existing architecture patterns and integrates seamlessly with the current authentication and CORS setup.
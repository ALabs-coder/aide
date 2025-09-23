# Security Guidelines

## Environment Variables

### Important Security Notes

- **NEVER** commit real API keys to version control
- The `.env` file contains real credentials and is gitignored
- Use `.env.example` as a template for setting up new environments

### Setup Instructions

1. Copy the example environment file:
   ```bash
   cp .env.example .env.local
   ```

2. Update `.env.local` with your actual values:
   ```bash
   VITE_API_BASE_URL=https://your-actual-api-gateway-url.execute-api.region.amazonaws.com/stage
   VITE_API_KEY=your-actual-api-key
   ```

3. The application will fail to start if required environment variables are missing

### Environment Variable Validation

The application includes runtime validation that will throw clear error messages if required environment variables are not set:

- `VITE_API_BASE_URL` - Required for API communication
- `VITE_API_KEY` - Required for API authentication

### Production Deployment

For production deployments:

1. Set environment variables in your deployment platform (Vercel, Netlify, etc.)
2. Never use development API keys in production
3. Ensure API keys have appropriate permissions and rotation policies

## Security Features

- ✅ No hardcoded credentials in source code
- ✅ Runtime environment validation
- ✅ Environment files gitignored
- ✅ Clear error messages for missing configuration
- ✅ No logging in production builds
# PDF Bank Statement UI

React + TypeScript frontend for uploading PDF bank statements to S3 and viewing processed data.

## Quick Start

```bash
# Install and run
npm install
npm run dev

# Access
http://localhost:5174
```

## Features

- **File Upload**: Drag & drop PDF files (max 10MB)
- **Real-time Feedback**: Upload progress and status
- **Data Display**: View uploaded files and processing status
- **Responsive Design**: Mobile-friendly interface

## Tech Stack

- **React 19** with TypeScript
- **Vite** for fast development
- **Tailwind CSS** for styling
- **Radix UI** components
- **Lucide React** icons

## Project Structure

```
src/
├── App.tsx                    # Main app with upload logic
├── components/
│   ├── ui/                    # Reusable UI components
│   ├── FileUploadModal.tsx    # File upload dialog
│   ├── Header.tsx             # App header
│   └── Footer.tsx             # App footer
└── main.tsx                   # App entry point
```

## Configuration

Set up environment variables for API configuration:

```bash
# Copy example and configure
cp .env.example .env
```

Required environment variables:
- `VITE_API_BASE_URL`: Your API Gateway URL
- `VITE_API_KEY`: Your API authentication key

Get these values from terraform:
```bash
terraform -chdir=../infrastructure output api_gateway_url
terraform -chdir=../infrastructure output api_key
```

## Development

```bash
# Install dependencies
npm install

# Configure environment (see Configuration section above)
cp .env.example .env

# Start dev server
npm run dev

# Build for deployment
npm run build

# Preview build
npm run preview

# Lint code
npm run lint
```

## API Integration

The UI uses a centralized API service layer for all API calls:

```typescript
// Import API service
import { apiService } from './services/api'

// Fetch data
const statements = await apiService.fetchStatements()

// Upload files
const presignedData = await apiService.getUploadUrl({ filename, content_type })
const result = await apiService.uploadFileToS3(presignedData.upload_url, file)
```

### API Configuration

All API configuration is centralized in `src/config/api.ts`:
- Base URL configuration with environment variable support
- API key management
- Request header standardization
- Endpoint definitions

### Error Handling

The API service includes structured error handling:
- Custom `ApiError` class for API-specific errors
- Consistent error messages across components
- Proper HTTP status code handling

---

**Related:** See `../api/README.md` for backend setup instructions.
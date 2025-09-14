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

## API Integration

The UI connects to the API server for file uploads:

```typescript
// Upload to S3 + DynamoDB
const response = await fetch('http://localhost:8001/upload', {
  method: 'POST',
  body: formData
});
```

## Development

```bash
# Start dev server
npm run dev

# Build for production  
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Environment Configuration

The app expects the API server running on `http://localhost:8001`. Update the fetch URL in `src/App.tsx` if using a different endpoint.

---

**Related:** See `../api/README.md` for backend setup instructions.
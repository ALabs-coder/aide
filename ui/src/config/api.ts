/**
 * API Configuration
 * Development environment configuration for API endpoints and keys
 */

export const API_CONFIG = {
  baseUrl: import.meta.env.VITE_API_BASE_URL,
  apiKey: import.meta.env.VITE_API_KEY,
} as const

// Runtime validation for required environment variables
if (!API_CONFIG.baseUrl) {
  throw new Error('VITE_API_BASE_URL environment variable is required')
}

if (!API_CONFIG.apiKey) {
  throw new Error('VITE_API_KEY environment variable is required')
}

// API Endpoints
export const API_ENDPOINTS = {
  statements: '/statements',
  upload: '/upload',
  extract: '/extract',
  health: '/health',
  statementData: '/statements/data',
  pdf: '/pdf',
  excelExport: '/statements/excel',
} as const

// Helper function to build full URLs
export const buildApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.baseUrl}${endpoint}`
}

// Common headers for API requests
export const getApiHeaders = (includeApiKey = false) => {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (includeApiKey) {
    headers['X-API-Key'] = API_CONFIG.apiKey
  }

  return headers
}
/**
 * API Service Layer
 * Centralized API calls with consistent error handling and request patterns
 */

import { buildApiUrl, getApiHeaders, API_ENDPOINTS } from '../config/api'

// Types
export interface BankStatement {
  id: string
  documentName: string
  dateUploaded: string | null
  dateProcessed: string | null
  fileSize?: number
  fileSizeBytes?: number
  status: string
  bankName?: string
  customerName?: string
  transactionCount?: number
  // New fields from job data
  error?: string
  processing_started_at?: string
  failed_at?: string
  metadata?: {
    has_password?: boolean
    api_version?: string
    upload_source?: string
  }
  job_type?: string
  content_type?: string
  // Financial summary from completed extractions
  financial_summary?: {
    closing_balance?: number
    date_range?: {
      from_date: string
      to_date: string
    }
    net_change?: number
    opening_balance?: number
    total_credits?: number
    total_debits?: number
    transaction_count?: number
  }
  total_transactions?: number
  statement_metadata?: {
    account_number?: string
    account_type?: string
    bank_name?: string
    currency?: string
    home_branch?: string
    ifsc_code?: string
  }
}

export interface DirectUploadResponse {
  job_id: string
  message: string
}

export interface Transaction {
  s_no: string
  date: string
  transaction_id: string
  remarks: string
  amount: string
  balance: string
  amount_numeric: number
  balance_numeric: number
  transaction_type: string
}

export interface ExtractResponse {
  success: boolean
  message: string
  total_transactions: number
  transactions: Transaction[]
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface PDFResponse {
  success: boolean
  job_id: string
  pdf_content: string
  content_type: string
  filename: string
}

export interface BankConfiguration {
  id: string
  name: string
}

export interface BankConfigurationsResponse {
  status: string
  data: BankConfiguration[]
  count: number
}

// Error handling
export class ApiError extends Error {
  public status?: number
  public response?: Response

  constructor(
    message: string,
    status?: number,
    response?: Response
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.response = response
  }
}

// Base API request handler with error handling
async function apiRequest<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  try {
    const headers = {
      ...getApiHeaders(true),
      ...options.headers,
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      // Try to get response body for better error details
      let errorBody = ''
      try {
        errorBody = await response.text()
      } catch (e) {
        // Could not read error body
      }

      throw new ApiError(
        `API request failed: ${response.status} ${response.statusText}${errorBody ? ` - ${errorBody}` : ''}`,
        response.status,
        response
      )
    }

    return await response.json()
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    throw new ApiError(
      error instanceof Error ? error.message : 'Unknown API error'
    )
  }
}

// API Service Functions
export const apiService = {
  // Fetch all bank statements
  async fetchStatements(): Promise<BankStatement[]> {
    const response = await apiRequest<{ statements: BankStatement[] }>(
      buildApiUrl(API_ENDPOINTS.statements)
    )
    return response.statements || []
  },

  // Upload file directly to backend
  async uploadFile(file: File, password?: string): Promise<DirectUploadResponse> {
    const formData = new FormData()
    formData.append('file', file)
    if (password) {
      formData.append('password', password)
    }

    try {
      const response = await fetch(buildApiUrl(API_ENDPOINTS.upload), {
        method: 'POST',
        headers: {
          'X-API-Key': getApiHeaders(true)['X-API-Key'],
        },
        body: formData,
      })

      if (!response.ok) {
        throw new ApiError(
          `Upload failed: ${response.statusText}`,
          response.status,
          response
        )
      }

      return await response.json()
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new ApiError(
        error instanceof Error ? error.message : 'Unknown upload error'
      )
    }
  },

  // Extract data from uploaded file
  async extractFile(file: File): Promise<ExtractResponse> {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(buildApiUrl(API_ENDPOINTS.extract), {
        method: 'POST',
        headers: {
          'X-API-Key': getApiHeaders(true)['X-API-Key'],
        },
        body: formData,
      })

      if (!response.ok) {
        throw new ApiError(
          `Extract failed: ${response.statusText}`,
          response.status,
          response
        )
      }

      return await response.json()
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new ApiError(
        error instanceof Error ? error.message : 'Unknown extract error'
      )
    }
  },

  // Fetch statement data by job ID
  async fetchStatementData(jobId: string): Promise<any> {
    const endpoint = API_ENDPOINTS.statementData
    const fullUrl = `${buildApiUrl(endpoint)}?job_id=${encodeURIComponent(jobId)}`
    try {
      const result = await apiRequest<any>(fullUrl)
      return result
    } catch (error) {
      throw error
    }
  },

  // Get PDF by job ID
  async getPDF(jobId: string): Promise<PDFResponse> {
    const endpoint = `${API_ENDPOINTS.pdf}/${jobId}`
    const fullUrl = buildApiUrl(endpoint)
    try {
      const result = await apiRequest<PDFResponse>(fullUrl)
      return result
    } catch (error) {
      throw error
    }
  },

  // Download Excel export
  async downloadExcel(jobId: string): Promise<void> {
    const endpoint = `${API_ENDPOINTS.excelExport}/${jobId}`
    const fullUrl = buildApiUrl(endpoint)

    try {
      const response = await fetch(fullUrl, {
        method: 'GET',
        headers: {
          'X-API-Key': getApiHeaders(true)['X-API-Key'],
        },
      })

      if (!response.ok) {
        throw new ApiError(
          `Excel download failed: ${response.statusText}`,
          response.status,
          response
        )
      }

      // Get filename from Content-Disposition header or create default
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = `bank_statement_${jobId}.xlsx`

      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^"]+)"?/)
        if (match) {
          filename = match[1]
        }
      }

      // Create blob and download
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (error) {
      if (error instanceof ApiError) {
        throw error
      }
      throw new ApiError(
        error instanceof Error ? error.message : 'Unknown Excel download error'
      )
    }
  },

  // Get active bank configurations
  async getBankConfigurations(): Promise<BankConfigurationsResponse> {
    return apiRequest<BankConfigurationsResponse>(
      buildApiUrl(API_ENDPOINTS.configurationsBank)
    )
  },

  // Health check
  async healthCheck(): Promise<{ status: string; version: string }> {
    return apiRequest<{ status: string; version: string }>(
      buildApiUrl(API_ENDPOINTS.health)
    )
  },
}
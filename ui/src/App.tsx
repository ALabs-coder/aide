import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Header } from './components/Header'
import { Footer } from './components/Footer'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './components/ui/table'
import { Badge } from './components/ui/badge'
import { Button } from './components/ui/button'
import { FileUploadModal } from './components/FileUploadModal'
import { SuccessDialog } from './components/SuccessDialog'
import { FileText, Building, Upload, Shield, AlertCircle, Clock, Info, Eye, Download, Loader2 } from 'lucide-react'
import { apiService, ApiError } from './services/api'
import type { BankStatement } from './services/api'

function App() {
  const navigate = useNavigate()
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  const [isSuccessDialogOpen, setIsSuccessDialogOpen] = useState(false)
  const [uploadedFileName, setUploadedFileName] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [bankStatements, setBankStatements] = useState<BankStatement[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [downloadingExcel, setDownloadingExcel] = useState<string | null>(null)
  
  const handleReset = () => {
    // No-op for simplified header
  }

  const fetchBankStatements = async () => {
    try {
      setLoading(true)
      setError(null)

      const statements = await apiService.fetchStatements()
      setBankStatements(statements)

    } catch (error) {
      const errorMessage = error instanceof ApiError
        ? error.message
        : 'Failed to fetch bank statements'
      setError(errorMessage)
      setBankStatements([])
    } finally {
      setLoading(false)
    }
  }

  // Fetch data on component mount
  useEffect(() => {
    fetchBankStatements()
  }, [])

  const handleFileUpload = async (file: File, password?: string) => {
    try {
      // Upload file directly to backend
      const result = await apiService.uploadFile(file, password)

      // Show success dialog instead of alert
      setUploadedFileName(file.name)
      setSuccessMessage(result.message || 'File uploaded successfully')
      setIsSuccessDialogOpen(true)

      // Refresh the statements list to show the newly uploaded file
      await fetchBankStatements()

    } catch (error) {
      const errorMessage = error instanceof ApiError
        ? error.message
        : 'Upload failed: Unknown error'
      alert(errorMessage)
    }
  }


  const handleViewResults = (statement: BankStatement) => {
    navigate(`/results/${statement.id}`)
  }

  const handleDownloadExcel = async (statement: BankStatement) => {
    setDownloadingExcel(statement.id)
    try {
      await apiService.downloadExcel(statement.id)
    } catch (error) {
      const errorMessage = error instanceof ApiError
        ? error.message
        : 'Excel download failed: Unknown error'
      alert(errorMessage)
    } finally {
      setDownloadingExcel(null)
    }
  }

  const getOverallStatus = (uploadStatus: string): string => {
    // Simply use the status from the database
    return uploadStatus
  }

  const getStatusBadge = (overallStatus: string) => {
    switch (overallStatus) {
      case 'uploaded':
        return <Badge variant="secondary" className="bg-blue-500 text-white hover:bg-blue-600">Queued</Badge>
      case 'processing':
        return <Badge variant="secondary" className="bg-yellow-500 text-white hover:bg-yellow-600">Processing</Badge>
      case 'completed':
        return <Badge variant="default" className="bg-green-500 hover:bg-green-600">Completed</Badge>
      case 'failed':
        return <Badge variant="destructive" className="bg-red-500 hover:bg-red-600">Failed</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  const formatDateTime = (dateString: string | null) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatFileSize = (sizeInMB: number | undefined, sizeInBytes: number | undefined) => {
    if (sizeInMB) {
      return `${sizeInMB} MB`
    }
    if (sizeInBytes) {
      const mb = (sizeInBytes / (1024 * 1024)).toFixed(2)
      return `${mb} MB`
    }
    return '-'
  }


  const getDetailsInfo = (statement: BankStatement) => {
    if (statement.status === 'failed' && statement.error) {
      return (
        <div className="flex items-start gap-1">
          <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm">
            <div className="text-red-600 font-medium">Error</div>
            <div className="text-muted-foreground text-xs max-w-[200px] truncate" title={statement.error}>
              {statement.error}
            </div>
          </div>
        </div>
      )
    }

    if (statement.status === 'completed') {
      // Show financial summary info for completed extractions
      const financial = statement.financial_summary
      const transactionCount = statement.total_transactions || financial?.transaction_count

      if (financial) {
        return (
          <div className="flex items-start gap-1">
            <Info className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
            <div className="text-sm">
              <div className="text-green-600 font-medium">
                {transactionCount} transactions
              </div>
              <div className="text-muted-foreground text-xs">
                Balance: ₹{financial.closing_balance?.toLocaleString('en-IN') || 'N/A'}
              </div>
            </div>
          </div>
        )
      }

      // Fallback if no financial summary
      return (
        <div className="flex items-start gap-1">
          <Info className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm">
            <div className="text-green-600 font-medium">Completed</div>
            <div className="text-muted-foreground text-xs">
              {transactionCount ? `${transactionCount} transactions` : 'Processed'}
            </div>
          </div>
        </div>
      )
    }

    if (statement.status === 'processing' && statement.processing_started_at) {
      return (
        <div className="flex items-start gap-1">
          <Clock className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm">
            <div className="text-blue-600 font-medium">Processing</div>
            <div className="text-muted-foreground text-xs">
              {formatDateTime(statement.processing_started_at)}
            </div>
          </div>
        </div>
      )
    }

    if (statement.metadata?.api_version) {
      return (
        <div className="flex items-start gap-1">
          <Info className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
          <div className="text-sm">
            <div className="text-gray-600 font-medium">API v{statement.metadata.api_version}</div>
            <div className="text-muted-foreground text-xs">
              {statement.metadata.upload_source?.replace('aws_', '') || 'Unknown'}
            </div>
          </div>
        </div>
      )
    }

    return '-'
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header
        hasResults={false}
        isProcessing={false}
        filename={undefined}
        onReset={handleReset}
      />

      <div className="flex-1 p-6">
        <div className="max-w-7xl mx-auto">
          {/* Page Header */}
          <div className="mb-8 flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">Bank Statements</h1>
              <p className="text-muted-foreground">Manage and view processed bank statement documents</p>
            </div>
            
            {/* Upload Button */}
            <Button 
              onClick={() => setIsUploadModalOpen(true)}
              className="flex items-center gap-2"
              size="lg"
            >
              <Upload className="w-5 h-5" />
              Upload Bank Statement
            </Button>
          </div>

          {/* Error State */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
              <p className="text-red-700">Error: {error}</p>
              <Button 
                variant="outline" 
                size="sm" 
                className="mt-2"
                onClick={fetchBankStatements}
              >
                Retry
              </Button>
            </div>
          )}

          {/* Statements Table */}
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[250px]">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      Document Name
                    </div>
                  </TableHead>
                  <TableHead>
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      Upload Time
                    </div>
                  </TableHead>
                  <TableHead>File Size</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>
                    <div className="flex items-center gap-2">
                      <AlertCircle className="w-4 h-4" />
                      Details
                    </div>
                  </TableHead>
                  <TableHead>
                    <div className="flex items-center gap-2">
                      <Building className="w-4 h-4" />
                      Bank
                    </div>
                  </TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      <div className="flex items-center justify-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
                        Loading bank statements...
                      </div>
                    </TableCell>
                  </TableRow>
                ) : bankStatements.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8">
                      <div className="text-muted-foreground">
                        <FileText className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                        <h3 className="text-lg font-medium mb-2">No bank statements found</h3>
                        <p>Upload your first bank statement to get started.</p>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  bankStatements.map((statement) => (
                    <TableRow key={statement.id}>
                      <TableCell className="font-medium">
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-muted-foreground" />
                          <span className="truncate max-w-[200px]" title={statement.documentName}>
                            {statement.documentName}
                          </span>
                          {statement.metadata?.has_password && (
                            <div title="Password protected">
                              <Shield className="w-3 h-3 text-green-600" />
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatDateTime(statement.dateUploaded)}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatFileSize(statement.fileSize, statement.fileSizeBytes)}
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(getOverallStatus(statement.status))}
                      </TableCell>
                      <TableCell>
                        {getDetailsInfo(statement)}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {statement.bankName || '-'}
                      </TableCell>
                      <TableCell>
                        {statement.status === 'completed' ? (
                          <div className="flex items-center gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleViewResults(statement)}
                              className="flex items-center gap-1"
                            >
                              <Eye className="w-4 h-4" />
                              View Results
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleDownloadExcel(statement)}
                              disabled={downloadingExcel === statement.id}
                              className="flex items-center gap-1"
                              title="Download Excel file"
                            >
                              {downloadingExcel === statement.id ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <Download className="w-4 h-4" />
                              )}
                              Excel
                            </Button>
                          </div>
                        ) : (
                          <span className="text-sm text-gray-500">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
      
      <Footer />

      <FileUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUpload={handleFileUpload}
      />

      <SuccessDialog
        isOpen={isSuccessDialogOpen}
        onClose={() => setIsSuccessDialogOpen(false)}
        fileName={uploadedFileName}
        message={successMessage}
      />
    </div>
  )
}

export default App
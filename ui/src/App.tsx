import { Header } from './components/Header'
import { Footer } from './components/Footer'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './components/ui/table'
import { Badge } from './components/ui/badge'
import { Button } from './components/ui/button'
import { FileUploadModal } from './components/FileUploadModal'
import { FileText, Building, User, Upload } from 'lucide-react'
import { useState } from 'react'

function App() {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false)
  
  const handleReset = () => {
    // No-op for simplified header
  }

  const handleFileUpload = async (file: File) => {
    console.log('Uploading file:', file.name)
    
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('X-API-KEY', 'test-key-123')
      
      const response = await fetch('http://localhost:8001/upload', {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }
      
      const result = await response.json()
      console.log('Upload successful:', result)
      
      // TODO: Update UI state with the new upload result
      alert(`Successfully uploaded ${file.name}! ${result.message || 'File processed successfully.'}`)
      
    } catch (error) {
      console.error('Upload error:', error)
      alert(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  // Mock data for bank statements
  const bankStatements = [
    {
      id: 1,
      documentName: "union_bank_statement_march_2024.pdf",
      dateUploaded: "2024-03-15",
      dateProcessed: "2024-03-15",
      status: "completed",
      bankName: "Union Bank of India",
      customerName: "John Doe"
    },
    {
      id: 2,
      documentName: "union_bank_statement_february_2024.pdf", 
      dateUploaded: "2024-02-28",
      dateProcessed: "2024-02-28",
      status: "completed",
      bankName: "Union Bank of India",
      customerName: "Sarah Johnson"
    },
    {
      id: 3,
      documentName: "bank_statement_april_2024.pdf",
      dateUploaded: "2024-04-10",
      dateProcessed: null,
      status: "processing",
      bankName: null,
      customerName: null
    },
    {
      id: 4,
      documentName: "corrupted_statement.pdf",
      dateUploaded: "2024-04-08",
      dateProcessed: "2024-04-08",
      status: "failed",
      bankName: null,
      customerName: null
    },
    {
      id: 5,
      documentName: "union_bank_statement_january_2024.pdf",
      dateUploaded: "2024-01-31",
      dateProcessed: "2024-01-31", 
      status: "completed",
      bankName: "Union Bank of India",
      customerName: "Michael Chen"
    }
  ]

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="default" className="bg-green-500 hover:bg-green-600">Completed</Badge>
      case 'processing':
        return <Badge variant="secondary" className="bg-yellow-500 text-white hover:bg-yellow-600">Processing</Badge>
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short', 
      day: 'numeric'
    })
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

          {/* Statements Table */}
          <div className="bg-card border border-border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[300px]">
                    <div className="flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      Document Name
                    </div>
                  </TableHead>
                  <TableHead>Date Uploaded</TableHead>
                  <TableHead>Date Processed</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>
                    <div className="flex items-center gap-2">
                      <Building className="w-4 h-4" />
                      Bank Name
                    </div>
                  </TableHead>
                  <TableHead>
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4" />
                      Customer Name
                    </div>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bankStatements.map((statement) => (
                  <TableRow key={statement.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-muted-foreground" />
                        <span className="truncate max-w-[250px]" title={statement.documentName}>
                          {statement.documentName}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(statement.dateUploaded)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(statement.dateProcessed)}
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(statement.status)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {statement.bankName || '-'}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {statement.customerName || '-'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Empty State (if no data) */}
          {bankStatements.length === 0 && (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">No bank statements found</h3>
              <p className="text-muted-foreground">Upload your first bank statement to get started.</p>
            </div>
          )}
        </div>
      </div>
      
      <Footer />

      <FileUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUpload={handleFileUpload}
      />
    </div>
  )
}

export default App
import { useState, useEffect } from 'react'
import { Button } from './ui/button'
import { ChevronLeft, ChevronRight, FileText, Loader2, X, ZoomIn, ZoomOut } from 'lucide-react'
import { apiService } from '../services/api'

interface PDFViewerProps {
  jobId: string | null
  isOpen: boolean
  onClose: () => void
  embedded?: boolean
  onPageChange?: (page: number) => void
  totalPages?: number
  onCollapseChange?: (isCollapsed: boolean) => void
}

export function PDFViewer({ jobId, isOpen, onClose, embedded = false, onPageChange, totalPages: propTotalPages, onCollapseChange }: PDFViewerProps) {
  const [pdfData, setPdfData] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [zoom, setZoom] = useState(1)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)

  useEffect(() => {
    if (jobId && isOpen) {
      fetchPDF()
    } else {
      setPdfData(null)
      setError(null)
    }
  }, [jobId, isOpen])

  const fetchPDF = async () => {
    if (!jobId) return

    try {
      setLoading(true)
      setError(null)

      const response = await apiService.getPDF(jobId)
      if (response.success && response.pdf_content) {
        setPdfData(response.pdf_content)
      } else {
        setError('Failed to load PDF content')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load PDF')
    } finally {
      setLoading(false)
    }
  }

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.2, 3))
  }

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 0.2, 0.5))
  }

  const toggleCollapsed = () => {
    const newCollapsedState = !isCollapsed
    setIsCollapsed(newCollapsedState)
    onCollapseChange?.(newCollapsedState)
  }

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage)
      onPageChange?.(newPage)
    }
  }

  const handlePrevPage = () => {
    handlePageChange(currentPage - 1)
  }

  const handleNextPage = () => {
    handlePageChange(currentPage + 1)
  }

  useEffect(() => {
    onPageChange?.(currentPage)
  }, [currentPage, onPageChange])

  useEffect(() => {
    if (propTotalPages) {
      setTotalPages(propTotalPages)
    }
  }, [propTotalPages])

  // Force iframe reload when page changes
  useEffect(() => {
    if (pdfData) {
      const iframe = document.querySelector('iframe[title="PDF Preview"]') as HTMLIFrameElement
      if (iframe) {
        const newSrc = `data:application/pdf;base64,${pdfData}#page=${currentPage}&toolbar=0&navpanes=0&scrollbar=0&view=FitH`
        if (iframe.src !== newSrc) {
          iframe.src = newSrc
        }
      }
    }
  }, [currentPage, pdfData])

  if (!isOpen) return null

  const containerClass = embedded
    ? 'h-full bg-white'
    : `fixed left-0 top-0 h-full bg-white border-r border-gray-200 shadow-lg z-40 transition-all duration-300 ${
        isCollapsed ? 'w-12' : 'w-[30%]'
      }`

  return (
    <div className={containerClass}>
      {/* Header */}
      <div className="h-20 border-b border-gray-200 px-4 bg-gray-50">
        {!isCollapsed && (
          <>
            <div className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-gray-600" />
                <span className="font-medium text-gray-900">PDF Preview</span>
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleZoomOut}
                  disabled={zoom <= 0.5}
                  className="h-8 w-8 p-0"
                >
                  <ZoomOut className="w-4 h-4" />
                </Button>
                <span className="text-xs text-gray-600 min-w-[3rem] text-center">
                  {Math.round(zoom * 100)}%
                </span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleZoomIn}
                  disabled={zoom >= 3}
                  className="h-8 w-8 p-0"
                >
                  <ZoomIn className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleCollapsed}
                  className="h-8 w-8 p-0"
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="h-8 w-8 p-0"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>
            {/* Page Navigation */}
            <div className="flex items-center justify-center gap-2 pb-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handlePrevPage}
                disabled={currentPage <= 1}
                className="h-8 w-8 p-0"
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="text-sm text-gray-700 min-w-[80px] text-center">
                Page {currentPage} of {totalPages}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleNextPage}
                disabled={currentPage >= totalPages}
                className="h-8 w-8 p-0"
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </>
        )}
        {isCollapsed && (
          <div className="flex items-center justify-center h-full">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleCollapsed}
              className="h-8 w-8 p-0"
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Content */}
      {!isCollapsed && (
        <div className="flex-1 h-[calc(100%-5rem)] overflow-hidden bg-gray-100">
          {loading && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-600" />
                <p className="text-gray-600">Loading PDF...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-center justify-center h-full">
              <div className="text-center p-6">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">Unable to load PDF</h3>
                <p className="text-gray-600 mb-4">{error}</p>
                <Button onClick={fetchPDF} variant="outline" size="sm">
                  Try Again
                </Button>
              </div>
            </div>
          )}

          {pdfData && !loading && !error && (
            <div className="h-full">
              <div
                className="bg-white mx-auto h-full"
                style={{
                  transform: `scale(${zoom})`,
                  transformOrigin: 'top center'
                }}
              >
                <iframe
                  key={`pdf-page-${currentPage}`}
                  src={`data:application/pdf;base64,${pdfData}#page=${currentPage}&toolbar=0&navpanes=0&scrollbar=0&view=FitH`}
                  className="w-full h-full border-0"
                  title="PDF Preview"
                  style={{
                    overflow: 'hidden'
                  }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Collapsed state indicator */}
      {isCollapsed && (
        <div className="flex flex-col items-center justify-center h-[calc(100%-5rem)] gap-2">
          <FileText className="w-6 h-6 text-gray-400" />
          <div className="writing-mode-vertical text-xs text-gray-500 transform rotate-90">
            PDF
          </div>
        </div>
      )}
    </div>
  )
}
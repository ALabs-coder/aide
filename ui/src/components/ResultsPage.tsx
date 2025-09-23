import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from './ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table'
import { PDFViewer } from './PDFViewer'
import { ArrowLeft, Home, FileText, Download, Loader2 } from 'lucide-react'
import { apiService, ApiError } from '../services/api'
import type { BankStatement } from '../services/api'

interface TransactionItem {
  "S.No": string
  "Date": string
  "Transaction_ID": string
  "Remarks": string
  "Amount": string
  "Balance": string
  "Amount_Numeric": number
  "Balance_Numeric": number
  "Transaction_Type": string
  "Page_Number": number
  // Formatted fields from backend
  formatted_txn_date?: string
  formatted_value_date?: string
  formatted_debit?: string
  formatted_credit?: string
  formatted_balance?: string
  formatted_amount?: string
  debit_amount?: string
  credit_amount?: string
}

interface StatementData {
  total_transactions: number
  processed_at: string
  statement_metadata: {
    bank_name: string
    currency: string
    address?: string
    mobile_number?: string
    home_branch?: string
    ifsc_code?: string
    account_type?: string
    account_number?: string
    statement_date?: string
    statement_period?: {
      from_date: string
      to_date: string
    }
  }
  financial_summary: {
    opening_balance: number
    closing_balance: number
    total_debits: number
    total_credits: number
    net_change: number
    transaction_count: number
    date_range: {
      from_date: string
      to_date: string
    }
  }
  transactions?: TransactionItem[]
}

export function ResultsPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [statement, setStatement] = useState<BankStatement | null>(null)
  const [statementData, setStatementData] = useState<StatementData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isPDFViewerOpen, setIsPDFViewerOpen] = useState(true)
  const [isPDFViewerCollapsed, setIsPDFViewerCollapsed] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [filteredTransactions, setFilteredTransactions] = useState<TransactionItem[]>([])
  const [totalPages, setTotalPages] = useState(1)
  const [isDownloadingCSV, setIsDownloadingCSV] = useState(false)

  useEffect(() => {
    const fetchStatementData = async () => {
      if (!id) {
        setError('No statement ID provided')
        setLoading(false)
        return
      }

      try {
        // First, get the statement details
        const statements = await apiService.fetchStatements()

        const foundStatement = statements.find(s => s.id === id)

        if (!foundStatement) {
          setError('Statement not found')
          setLoading(false)
          return
        }

        setStatement(foundStatement)

        // Fetch actual statement data from API
        const response = await apiService.fetchStatementData(id)
        setStatementData(response.data)

        // Calculate total pages and set initial filtered transactions
        if (response.data.transactions && response.data.transactions.length > 0) {
          const pages = Math.max(...response.data.transactions.map((t: TransactionItem) => t.Page_Number))
          setTotalPages(pages)
          setFilteredTransactions(response.data.transactions.filter((t: TransactionItem) => t.Page_Number === 1))
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch statement data')
      } finally {
        setLoading(false)
      }
    }

    fetchStatementData()
  }, [id])

  // Filter transactions when page changes
  useEffect(() => {
    if (statementData?.transactions) {
      const pageTransactions = statementData.transactions.filter((t: TransactionItem) => t.Page_Number === currentPage)
      setFilteredTransactions(pageTransactions)
    }
  }, [currentPage, statementData])

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const handlePDFViewerCollapseChange = (isCollapsed: boolean) => {
    setIsPDFViewerCollapsed(isCollapsed)
  }

  const handleDownloadCSV = async () => {
    if (!id) return

    setIsDownloadingCSV(true)
    try {
      await apiService.downloadCSV(id)
    } catch (error) {
      const errorMessage = error instanceof ApiError
        ? error.message
        : 'CSV download failed: Unknown error'
      alert(errorMessage)
    } finally {
      setIsDownloadingCSV(false)
    }
  }

  const getPageSpecificSummary = () => {
    if (!statementData?.transactions) return null

    const pageTransactions = filteredTransactions
    const totalAmount = pageTransactions.reduce((sum, t) => sum + t.Amount_Numeric, 0)
    const creditCount = pageTransactions.filter(t => t.Transaction_Type === 'Credit').length
    const debitCount = pageTransactions.filter(t => t.Transaction_Type === 'Debit').length

    return {
      count: pageTransactions.length,
      totalAmount,
      creditCount,
      debitCount
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2
    }).format(amount)
  }


  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        {/* Header with Navigation */}
        <div className="border-b bg-card">
          <div className="w-full px-6 py-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-4">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => navigate('/')}
                  className="flex items-center gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back
                </Button>
                <div>
                  <h1 className="text-xl font-semibold">Statement Results</h1>
                  <p className="text-sm text-muted-foreground">Loading...</p>
                </div>
                {/* Loading Financial Summary Placeholder */}
                <div className="flex items-center gap-4 ml-8 text-sm animate-pulse">
                  <div className="h-4 w-20 bg-gray-300 rounded"></div>
                  <div className="h-4 w-20 bg-gray-300 rounded"></div>
                  <div className="h-4 w-20 bg-gray-300 rounded"></div>
                </div>
              </div>
              <Button
                variant="outline"
                onClick={() => navigate('/')}
                className="flex items-center gap-2"
              >
                <Home className="w-4 h-4" />
                Home
              </Button>
            </div>

          </div>
        </div>

        {/* Loading Content */}
        <div className="w-full px-6 py-6">
          <div className="flex items-center justify-center h-96">
            <div className="flex items-center gap-2">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
              <span>Loading statement results...</span>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (error || !statement || !statementData) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold mb-2">Error</h2>
          <p className="text-muted-foreground mb-4">{error || 'Statement data not found'}</p>
          <Button onClick={() => navigate('/')} variant="outline">
            <Home className="w-4 h-4 mr-2" />
            Go Home
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header with Navigation */}
      <div className="border-b bg-card">
        <div className="w-full px-6 py-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/')}
                className="flex items-center gap-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </Button>
              <div>
                <h1 className="text-xl font-semibold">Statement Results</h1>
                <p className="text-sm text-muted-foreground">{statement.documentName}</p>
              </div>
              {/* Financial Summary inline with title */}
              <div className="flex items-center gap-4 ml-8 text-sm">
                <span>Opening: <span className="font-medium">{formatCurrency(statementData.financial_summary.opening_balance)}</span></span>
                <span className={`${statementData.financial_summary.net_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  Net: <span className="font-medium">{statementData.financial_summary.net_change >= 0 ? '+' : ''}{formatCurrency(statementData.financial_summary.net_change)}</span>
                </span>
                <span className="text-green-600">CR: <span className="font-medium">+{formatCurrency(statementData.financial_summary.total_credits)}</span></span>
                <span className="text-red-600">DR: <span className="font-medium">{formatCurrency(statementData.financial_summary.total_debits)}</span></span>
                <span>Closing: <span className="font-semibold">{formatCurrency(statementData.financial_summary.closing_balance)}</span></span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                onClick={handleDownloadCSV}
                disabled={isDownloadingCSV}
                className="flex items-center gap-2"
                title="Download CSV for Tally import"
              >
                {isDownloadingCSV ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Download className="w-4 h-4" />
                )}
                {isDownloadingCSV ? 'Exporting...' : 'Export CSV'}
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate('/')}
                className="flex items-center gap-2"
              >
                <Home className="w-4 h-4" />
                Home
              </Button>
            </div>
          </div>

        </div>
      </div>

      {/* Main Content */}
      <div className="w-full px-6 py-4">

        {/* Main Content Area with PDF Viewer and Transactions */}
        <div className="flex gap-6 h-[calc(100vh-200px)]">
          {/* PDF Viewer Section - 35% width */}
          <div className={`transition-all duration-300 ${isPDFViewerOpen && !isPDFViewerCollapsed ? 'w-[35%]' : isPDFViewerOpen && isPDFViewerCollapsed ? 'w-12' : 'w-0'} ${isPDFViewerOpen ? 'block' : 'hidden'}`}>
            <div className="h-full bg-white border rounded-lg overflow-hidden">
              <PDFViewer
                jobId={id || null}
                isOpen={isPDFViewerOpen}
                onClose={() => setIsPDFViewerOpen(false)}
                embedded={true}
                onPageChange={handlePageChange}
                totalPages={totalPages}
                onCollapseChange={handlePDFViewerCollapseChange}
              />
            </div>
          </div>

          {/* Transactions Section - Remaining width */}
          <div className={`transition-all duration-300 ${isPDFViewerOpen && !isPDFViewerCollapsed ? 'w-[65%]' : isPDFViewerOpen && isPDFViewerCollapsed ? 'w-[calc(100%-3rem)]' : 'w-full'}`}>
            <div className="bg-card border rounded-lg h-full flex flex-col">
              {/* Header with page-specific metadata */}
              <div className="border-b px-4 py-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <h3 className="text-lg font-semibold">Transactions</h3>
                    {statementData && (
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <span className="font-medium">Page {currentPage}</span>
                        <span>•</span>
                        <span>{filteredTransactions.length} transactions</span>
                        {(() => {
                          const summary = getPageSpecificSummary()
                          return summary && (
                            <>
                              <span>•</span>
                              <span className="text-green-600">{summary.creditCount} CR</span>
                              <span>•</span>
                              <span className="text-red-600">{summary.debitCount} DR</span>
                            </>
                          )
                        })()}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {statementData && (
                      <div className="flex items-center gap-4 text-xs text-muted-foreground">
                        <span>{statementData.statement_metadata.bank_name}</span>
                        <span>AC# {statementData.statement_metadata.account_number}</span>
                        <span>{statementData.statement_metadata.ifsc_code}</span>
                        <span>{statementData.statement_metadata.home_branch}</span>
                      </div>
                    )}
                    {!isPDFViewerOpen && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setIsPDFViewerOpen(true)
                          setIsPDFViewerCollapsed(false)
                        }}
                        className="flex items-center gap-2"
                      >
                        <FileText className="w-4 h-4" />
                        Show PDF
                      </Button>
                    )}
                  </div>
                </div>
              </div>

              {/* Transactions Table */}
              <div className="flex-1 overflow-auto">
                {filteredTransactions && filteredTransactions.length > 0 ? (
                  <div className="w-full">
                    <Table className="table-fixed w-full">
                    <TableHeader>
                      <TableRow className="hover:bg-transparent">
                        <TableHead className="w-16 text-center">#</TableHead>
                        <TableHead className="w-28">Txn Date</TableHead>
                        <TableHead className="w-28">Value Date</TableHead>
                        <TableHead className="w-80 min-w-0">Description</TableHead>
                        <TableHead className="w-32 text-right">Debit</TableHead>
                        <TableHead className="w-32 text-right">Credit</TableHead>
                        <TableHead className="w-32 text-right">Balance</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredTransactions.map((transaction, index) => (
                        <TableRow key={`${transaction['S.No']}-${index}`} className="hover:bg-muted/50">
                          <TableCell className="text-center text-sm font-medium">
                            {transaction['S.No']}
                          </TableCell>
                          <TableCell className="text-sm font-mono">
                            {transaction.Date}
                          </TableCell>
                          <TableCell className="text-sm font-mono">
                            {transaction.Date}
                          </TableCell>
                          <TableCell className="text-sm min-w-0">
                            <div className="truncate" title={transaction.Remarks}>
                              {transaction.Remarks}
                            </div>
                          </TableCell>
                          <TableCell className="text-sm font-mono text-right text-red-600 font-medium">
                            {transaction.debit_amount || ''}
                          </TableCell>
                          <TableCell className="text-sm font-mono text-right text-green-600 font-medium">
                            {transaction.credit_amount || ''}
                          </TableCell>
                          <TableCell className="text-sm font-mono text-right font-medium">
                            {transaction.formatted_balance || transaction.Balance?.replace(/\s*\(?\s*(DR|dr|Dr|CR|cr|Cr)\s*\)?\s*/g, '').trim() || ''}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                    </Table>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <FileText className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <h4 className="text-lg font-medium mb-2">No Transactions</h4>
                    <p className="text-muted-foreground">
                      {currentPage > 1
                        ? `No transactions found on page ${currentPage}.`
                        : 'No transaction data available for this statement.'
                      }
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
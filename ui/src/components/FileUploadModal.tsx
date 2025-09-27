import { useState, useCallback, useEffect } from 'react'
import { useDropzone, type FileRejection } from 'react-dropzone'
import { Upload, FileText, X, AlertCircle, Loader2, Lock, Building } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Alert, AlertDescription } from './ui/alert'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select'
import { Skeleton } from './ui/skeleton'
import { type BankConfiguration } from '../services/api'
import { bankCache } from '../services/bankCache'

interface FileUploadModalProps {
  isOpen: boolean
  onClose: () => void
  onUpload: (file: File, bankId: string, password?: string) => Promise<void>
}

export function FileUploadModal({ isOpen, onClose, onUpload }: FileUploadModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [selectedBank, setSelectedBank] = useState<string>('')
  const [banks, setBanks] = useState<BankConfiguration[]>([])
  const [loadingBanks, setLoadingBanks] = useState(false)
  const [banksError, setBanksError] = useState<string>('')
  const [isPasswordProtected, setIsPasswordProtected] = useState<'yes' | 'no' | null>(null)
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string>('')
  const [isUploading, setIsUploading] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
    setError('')
    
    if (rejectedFiles.length > 0) {
      const rejectedFile = rejectedFiles[0]
      if (rejectedFile.errors[0]?.code === 'file-invalid-type') {
        setError('Only PDF files are allowed.')
      } else if (rejectedFile.errors[0]?.code === 'file-too-large') {
        setError('File is too large. Maximum size is 10MB.')
      } else {
        setError('Invalid file. Please select a valid PDF file.')
      }
      return
    }

    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0])
    }
  }, [])

  // Fetch banks when modal opens with caching
  useEffect(() => {
    if (isOpen) {
      // Immediately show cached data if available
      const cachedBanks = bankCache.getCachedBanks()
      if (cachedBanks.length > 0) {
        setBanks(cachedBanks)
      }

      // Always try to fetch fresh data (will use cache if valid)
      fetchBanks()
    }
  }, [isOpen])

  const fetchBanks = async () => {
    setLoadingBanks(bankCache.isLoading())
    setBanksError('')

    try {
      const freshBanks = await bankCache.getBanks()
      setBanks(freshBanks)
    } catch (error) {
      setBanksError('Unable to load banks. Please check your connection.')
      console.error('Failed to fetch banks:', error)
    } finally {
      setLoadingBanks(false)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  })

  const handleUpload = async () => {
    if (selectedFile) {
      // Validation: bank selection is required
      if (!selectedBank) {
        setError('Please select a bank from the list')
        return
      }

      // Validation: user must select password protection option
      if (isPasswordProtected === null) {
        setError('Please select whether the PDF is password protected')
        return
      }

      // Validation: if password protection is "yes", password is required
      if (isPasswordProtected === 'yes' && !password.trim()) {
        setError('Password is required for password-protected PDFs')
        return
      }

      try {
        setIsUploading(true)
        setError('')
        const finalPassword = isPasswordProtected === 'yes' ? password.trim() : undefined
        await onUpload(selectedFile, selectedBank, finalPassword)
        handleClose()
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Upload failed')
      } finally {
        setIsUploading(false)
      }
    }
  }

  const handleClose = () => {
    if (isUploading) return
    setSelectedFile(null)
    setSelectedBank('')
    setIsPasswordProtected(null)
    setPassword('')
    setError('')
    setIsUploading(false)
    onClose()
  }

  const removeFile = () => {
    setSelectedFile(null)
    setError('')
  }

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Upload Bank Statement
          </DialogTitle>
          <DialogDescription>
            Select a PDF file to upload. Only PDF files are supported.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {!selectedFile ? (
            <div
              {...getRootProps()}
              className={`
                border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
                ${isDragActive 
                  ? 'border-primary bg-primary/5' 
                  : 'border-muted-foreground/25 hover:border-primary hover:bg-accent/50'
                }
              `}
            >
              <input {...getInputProps()} />
              <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                  <Upload className="w-6 h-6 text-primary" />
                </div>
                
                {isDragActive ? (
                  <div>
                    <p className="text-sm font-medium">Drop the PDF file here</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <p className="text-sm font-medium">
                      Drag & drop a PDF file here, or{' '}
                      <span className="text-primary">click to browse</span>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Maximum file size: 10MB
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded bg-red-50 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-red-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium truncate max-w-[200px]">
                      {selectedFile.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={removeFile}
                  className="h-8 w-8 p-0"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}

          {selectedFile && (
            <FileConfigurationSection
              loadingBanks={loadingBanks}
              banksError={banksError}
              banks={banks}
              selectedBank={selectedBank}
              setSelectedBank={setSelectedBank}
              isPasswordProtected={isPasswordProtected}
              setIsPasswordProtected={setIsPasswordProtected}
              password={password}
              setPassword={setPassword}
              isUploading={isUploading}
              onRetryBanks={() => {
                bankCache.clearCache()
                fetchBanks()
              }}
            />
          )}

        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button variant="outline" onClick={handleClose} disabled={isUploading}>
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || !selectedBank || isUploading || isPasswordProtected === null}
            className="flex items-center gap-2"
          >
            {isUploading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Upload className="w-4 h-4" />
            )}
            {isUploading ? 'Uploading...' : 'Upload Statement'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

interface FileConfigurationSectionProps {
  loadingBanks: boolean
  banksError: string
  banks: BankConfiguration[]
  selectedBank: string
  setSelectedBank: (bank: string) => void
  isPasswordProtected: 'yes' | 'no' | null
  setIsPasswordProtected: (value: 'yes' | 'no') => void
  password: string
  setPassword: (password: string) => void
  isUploading: boolean
  onRetryBanks: () => void
}

function FileConfigurationSection({
  loadingBanks,
  banksError,
  banks,
  selectedBank,
  setSelectedBank,
  isPasswordProtected,
  setIsPasswordProtected,
  password,
  setPassword,
  isUploading,
  onRetryBanks
}: FileConfigurationSectionProps) {
  return (
    <div className="space-y-4">
      <BankSelectionSection
        loadingBanks={loadingBanks}
        banksError={banksError}
        banks={banks}
        selectedBank={selectedBank}
        setSelectedBank={setSelectedBank}
        isUploading={isUploading}
        onRetryBanks={onRetryBanks}
      />

      <PasswordProtectionSection
        isPasswordProtected={isPasswordProtected}
        setIsPasswordProtected={setIsPasswordProtected}
        password={password}
        setPassword={setPassword}
        isUploading={isUploading}
      />
    </div>
  )
}

interface BankSelectionSectionProps {
  loadingBanks: boolean
  banksError: string
  banks: BankConfiguration[]
  selectedBank: string
  setSelectedBank: (bank: string) => void
  isUploading: boolean
  onRetryBanks: () => void
}

function BankSelectionSection({
  loadingBanks,
  banksError,
  banks,
  selectedBank,
  setSelectedBank,
  isUploading,
  onRetryBanks
}: BankSelectionSectionProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium flex items-center gap-2">
        <Building className="w-4 h-4" />
        Select Bank
        <span className="text-red-500">*</span>
      </label>

      {loadingBanks ? (
        <BankLoadingState />
      ) : banksError ? (
        <BankErrorState error={banksError} onRetry={onRetryBanks} />
      ) : (
        <BankSelector
          banks={banks}
          selectedBank={selectedBank}
          setSelectedBank={setSelectedBank}
          isUploading={isUploading}
        />
      )}

      <p className="text-xs text-muted-foreground">
        Choose the bank that issued this statement
      </p>
    </div>
  )
}

function BankLoadingState() {
  return (
    <div className="space-y-2">
      <Skeleton className="h-10 w-full" />
      <div className="flex items-center gap-2">
        <Loader2 className="w-3 h-3 animate-spin" />
        <span className="text-xs text-muted-foreground">Loading banks...</span>
      </div>
    </div>
  )
}

function BankErrorState({ error, onRetry }: { error: string; onRetry: () => void }) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertDescription className="flex items-center justify-between">
        <span>{error}</span>
        <Button size="sm" variant="outline" onClick={onRetry}>
          Retry
        </Button>
      </AlertDescription>
    </Alert>
  )
}

function BankSelector({
  banks,
  selectedBank,
  setSelectedBank,
  isUploading
}: {
  banks: BankConfiguration[]
  selectedBank: string
  setSelectedBank: (bank: string) => void
  isUploading: boolean
}) {
  return (
    <Select value={selectedBank} onValueChange={setSelectedBank} disabled={isUploading}>
      <SelectTrigger>
        <SelectValue placeholder={`Select from ${banks.length} banks`} />
      </SelectTrigger>
      <SelectContent>
        {banks.map(bank => (
          <SelectItem key={bank.id} value={bank.id}>
            {bank.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

interface PasswordProtectionSectionProps {
  isPasswordProtected: 'yes' | 'no' | null
  setIsPasswordProtected: (value: 'yes' | 'no') => void
  password: string
  setPassword: (password: string) => void
  isUploading: boolean
}

function PasswordProtectionSection({
  isPasswordProtected,
  setIsPasswordProtected,
  password,
  setPassword,
  isUploading
}: PasswordProtectionSectionProps) {
  return (
    <div className="space-y-3">
      <label className="text-sm font-medium flex items-center gap-2">
        <Lock className="w-4 h-4" />
        Is this PDF password protected?
      </label>

      <PasswordRadioButtons
        isPasswordProtected={isPasswordProtected}
        setIsPasswordProtected={setIsPasswordProtected}
        isUploading={isUploading}
      />

      {isPasswordProtected === 'yes' && (
        <PasswordInputSection
          password={password}
          setPassword={setPassword}
          isUploading={isUploading}
        />
      )}
    </div>
  )
}

function PasswordRadioButtons({
  isPasswordProtected,
  setIsPasswordProtected,
  isUploading
}: {
  isPasswordProtected: 'yes' | 'no' | null
  setIsPasswordProtected: (value: 'yes' | 'no') => void
  isUploading: boolean
}) {
  return (
    <div className="flex gap-6">
      <div className="flex items-center space-x-2">
        <input
          type="radio"
          id="password-yes"
          name="password-protection"
          value="yes"
          checked={isPasswordProtected === 'yes'}
          onChange={() => setIsPasswordProtected('yes')}
          disabled={isUploading}
          className="w-4 h-4 text-primary border-gray-300 focus:ring-primary"
        />
        <label htmlFor="password-yes" className="text-sm font-medium">
          Yes
        </label>
      </div>
      <div className="flex items-center space-x-2">
        <input
          type="radio"
          id="password-no"
          name="password-protection"
          value="no"
          checked={isPasswordProtected === 'no'}
          onChange={() => setIsPasswordProtected('no')}
          disabled={isUploading}
          className="w-4 h-4 text-primary border-gray-300 focus:ring-primary"
        />
        <label htmlFor="password-no" className="text-sm font-medium">
          No
        </label>
      </div>
    </div>
  )
}

function PasswordInputSection({
  password,
  setPassword,
  isUploading
}: {
  password: string
  setPassword: (password: string) => void
  isUploading: boolean
}) {
  return (
    <div className="space-y-2">
      <label htmlFor="password" className="text-sm font-medium">
        Enter PDF Password
      </label>
      <Input
        id="password"
        type="password"
        placeholder="Enter PDF password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        disabled={isUploading}
        className="w-full"
      />
      <p className="text-xs text-muted-foreground">
        This password is required to unlock and process your PDF
      </p>
    </div>
  )
}
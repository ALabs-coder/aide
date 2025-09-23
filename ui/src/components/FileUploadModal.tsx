import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, AlertCircle, Loader2, Lock } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/dialog'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Alert, AlertDescription } from './ui/alert'

interface FileUploadModalProps {
  isOpen: boolean
  onClose: () => void
  onUpload: (file: File, password?: string) => Promise<void>
}

export function FileUploadModal({ isOpen, onClose, onUpload }: FileUploadModalProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isPasswordProtected, setIsPasswordProtected] = useState<'yes' | 'no' | null>(null)
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string>('')
  const [isUploading, setIsUploading] = useState(false)

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
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
        await onUpload(selectedFile, finalPassword)
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
            <div className="space-y-4">
              <div className="space-y-3">
                <label className="text-sm font-medium flex items-center gap-2">
                  <Lock className="w-4 h-4" />
                  Is this PDF password protected?
                </label>
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
              </div>

              {isPasswordProtected === 'yes' && (
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
              )}
            </div>
          )}

        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button variant="outline" onClick={handleClose} disabled={isUploading}>
            Cancel
          </Button>
          <Button
            onClick={handleUpload}
            disabled={!selectedFile || isUploading || isPasswordProtected === null}
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
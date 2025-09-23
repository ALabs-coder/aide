import { CheckCircle, FileText } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog'
import { Button } from './ui/button'

interface SuccessDialogProps {
  isOpen: boolean
  onClose: () => void
  fileName: string
  message?: string
}

export function SuccessDialog({ isOpen, onClose, fileName }: SuccessDialogProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md max-h-[90vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-green-700">
            <CheckCircle className="w-5 h-5 text-green-600" />
            Upload Successful
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded bg-green-100 flex items-center justify-center flex-shrink-0">
                <FileText className="w-5 h-5 text-green-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-green-800 mb-2">
                  File uploaded successfully
                </p>
                <p className="text-sm text-green-700 break-all" title={fileName}>
                  <strong>{fileName}</strong>
                </p>
              </div>
            </div>
          </div>

          <div className="text-sm text-muted-foreground">
            Your bank statement has been uploaded and is ready for processing.
          </div>

          <div className="flex justify-end pt-2">
            <Button onClick={onClose} className="bg-green-600 hover:bg-green-700">
              Continue
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
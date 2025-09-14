import React from 'react'
import { FileText, RotateCcw, Database, Activity } from 'lucide-react'
import { Button } from './ui/button'
import { Badge } from './ui/badge'

interface HeaderProps {
  hasResults: boolean
  isProcessing: boolean
  filename?: string
  onReset: () => void
}

export function Header({ 
  hasResults, 
  isProcessing, 
  filename,
  onReset 
}: HeaderProps) {
  return (
    <header className="h-[60px] bg-background border-b border-border/50 flex items-center justify-between px-6 panel-shadow">
      {/* Brand Section */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <FileText className="w-4 h-4 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-[20px] font-semibold text-foreground">
              Bank Statement OCR Processor
            </h1>
            <p className="text-xs text-muted-foreground">
              Supported Banks: Union Bank
            </p>
          </div>
        </div>
        
        {/* Status Indicators */}
        <div className="flex items-center gap-2 ml-4">
          {isProcessing && (
            <Badge variant="secondary" className="flex items-center gap-1.5 animate-pulse">
              <Activity className="w-3 h-3" />
              Processing
            </Badge>
          )}
          
        </div>
      </div>

      {/* Action Section */}
      <div className="flex items-center gap-3">
        {filename && (
          <div className="hidden sm:flex items-center gap-2 text-sm text-muted-foreground">
            <FileText className="w-4 h-4" />
            <span className="max-w-[200px] truncate">{filename}</span>
          </div>
        )}
        
        {(hasResults || isProcessing) && (
          <Button 
            variant="outline" 
            size="sm"
            onClick={onReset}
            disabled={isProcessing}
            className="flex items-center gap-2 transition-fast hover:bg-accent"
          >
            <RotateCcw className="w-4 h-4" />
            <span className="hidden sm:inline">Reset</span>
          </Button>
        )}
      </div>
    </header>
  )
}
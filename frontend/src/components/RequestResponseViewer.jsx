import React, { useState } from 'react'
import { Card, CardContent } from './ui/card'
import { Button } from './ui/button'
import { ChevronDown, ChevronUp, Code, FileJson } from 'lucide-react'

export default function RequestResponseViewer({ request, response }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [activeTab, setActiveTab] = useState('request')

  if (!request && !response) {
    return null
  }

  return (
    <Card className="shadow-md overflow-hidden">
      <Button
        onClick={() => setIsExpanded(!isExpanded)}
        variant="ghost"
        className="w-full justify-between h-12 bg-primary hover:bg-primary/90 text-primary-foreground rounded-none"
      >
        <span className="flex items-center gap-2 font-semibold">
          <Code className="w-4 h-4" />
          {isExpanded ? 'Hide' : 'Show'} Request/Response
        </span>
        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </Button>

      {isExpanded && (
        <div className="animate-slide-down">
          <div className="flex border-b border-border bg-muted">
            <button
              className={`flex-1 py-3 text-sm font-semibold transition-all ${
                activeTab === 'request'
                  ? 'bg-card text-foreground border-b-2 border-primary'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/80'
              }`}
              onClick={() => setActiveTab('request')}
            >
              <span className="flex items-center justify-center gap-2">
                <FileJson className="w-4 h-4" />
                Request
              </span>
            </button>
            <button
              className={`flex-1 py-3 text-sm font-semibold transition-all ${
                activeTab === 'response'
                  ? 'bg-card text-foreground border-b-2 border-primary'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/80'
              }`}
              onClick={() => setActiveTab('response')}
            >
              <span className="flex items-center justify-center gap-2">
                <FileJson className="w-4 h-4" />
                Response
              </span>
            </button>
          </div>

          <div className="max-h-96 overflow-y-auto bg-[#0d1117]">
            {activeTab === 'request' && request && (
              <pre className="p-4 text-xs font-mono text-emerald-300 whitespace-pre overflow-x-auto">
                {JSON.stringify(request, null, 2)}
              </pre>
            )}
            {activeTab === 'response' && response && (
              <pre className="p-4 text-xs font-mono text-emerald-300 whitespace-pre overflow-x-auto">
                {JSON.stringify(response, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </Card>
  )
}

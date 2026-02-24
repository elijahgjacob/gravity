import React, { useState } from 'react'
import axios from 'axios'
import QueryInput from './components/QueryInput'
import ResultsDisplay from './components/ResultsDisplay'
import MetricsPanel from './components/MetricsPanel'
import RequestResponseViewer from './components/RequestResponseViewer'
import UserSummaryPanel from './components/UserSummaryPanel'
import ThemeToggle from './components/ThemeToggle'
import { Card } from './components/ui/card'
import { Badge } from './components/ui/badge'
import { Zap, Target, Database } from 'lucide-react'

function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [latency, setLatency] = useState(null)
  const [lastRequest, setLastRequest] = useState(null)
  const [lastResponse, setLastResponse] = useState(null)
  const [selectedUserIdForSearch, setSelectedUserIdForSearch] = useState(null)

  const handleSearch = async (requestData) => {
    const payload = { ...requestData }
    if (selectedUserIdForSearch) payload.user_id = selectedUserIdForSearch
    setLoading(true)
    setError(null)
    setLastRequest(payload)
    
    const startTime = performance.now()
    
    try {
      const response = await axios.post('/api/retrieve', payload)
      const endTime = performance.now()
      
      setResults(response.data)
      setLatency(response.data.latency_ms)
      setLastResponse(response.data)
      
      console.log('Search completed:', {
        query: payload.query,
        user_id: payload.user_id,
        serverLatency: response.data.latency_ms,
        clientLatency: endTime - startTime,
        campaigns: response.data.campaigns.length
      })
    } catch (err) {
      console.error('Search error:', err)
      setError(err.response?.data?.detail || err.message || 'An error occurred')
      setLastResponse(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent mb-2">
                Gravity
              </h1>
              <p className="text-muted-foreground text-lg">High-Performance Ad Retrieval System</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex gap-3">
                <Badge variant="secondary" className="flex items-center gap-1.5 px-3 py-1.5 text-xs">
                  <Database className="w-3.5 h-3.5" />
                  10,000 Campaigns
                </Badge>
                <Badge variant="secondary" className="flex items-center gap-1.5 px-3 py-1.5 text-xs">
                  <Target className="w-3.5 h-3.5" />
                  &lt; 100ms p95
                </Badge>
                <Badge variant="secondary" className="flex items-center gap-1.5 px-3 py-1.5 text-xs">
                  <Zap className="w-3.5 h-3.5" />
                  384D Vector
                </Badge>
              </div>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 py-8 px-6">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-[1fr_340px] gap-6">
          <div className="space-y-6 min-w-0">
            <div className="animate-slide-down">
              <UserSummaryPanel onSelectUser={setSelectedUserIdForSearch} />
            </div>

            <Card className="animate-slide-down shadow-md">
              <div className="p-6">
                <h2 className="text-2xl font-semibold mb-4 text-foreground">Search Query</h2>
                <QueryInput onSubmit={handleSearch} loading={loading} />
              </div>
            </Card>

            {error && (
              <Card className="border-destructive/50 bg-destructive/10 animate-slide-down">
                <div className="p-4">
                  <p className="text-destructive font-medium"><strong>Error:</strong> {error}</p>
                </div>
              </Card>
            )}

            <div className="animate-slide-up">
              <h2 className="text-2xl font-semibold mb-4 text-foreground px-1">
                {results ? `Results (${results.campaigns.length} campaigns)` : 'Results'}
              </h2>
              <ResultsDisplay results={results} />
            </div>

            <div className="animate-slide-up">
              <RequestResponseViewer 
                request={lastRequest}
                response={lastResponse}
              />
            </div>
          </div>

          <aside className="lg:sticky lg:top-24 h-fit space-y-4">
            <div className="animate-fade-in">
              <MetricsPanel 
                metrics={results?.metadata} 
                latency={latency}
              />
            </div>
          </aside>
        </div>
      </main>

      <footer className="border-t border-border bg-card text-muted-foreground py-6 px-6 text-center text-sm">
        <p>
          Powered by FastAPI + React | 
          <a href="/api/docs" target="_blank" rel="noopener noreferrer" className="text-foreground hover:underline ml-2"> API Docs</a> | 
          <a href="https://github.com/elijahgjacob/gravity" target="_blank" rel="noopener noreferrer" className="text-foreground hover:underline ml-2"> GitHub</a>
        </p>
      </footer>
    </div>
  )
}

export default App

import React, { useState, useEffect } from 'react'
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
  const [searchSuccessWithUserId, setSearchSuccessWithUserId] = useState(null)
  const [serverWarmedUp, setServerWarmedUp] = useState(false)
  const [warmupStatus, setWarmupStatus] = useState('warming')
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  // Warmup: Call warmup endpoint on page load to prevent cold starts
  useEffect(() => {
    const warmupServer = async () => {
      try {
        setWarmupStatus('warming')
        const startTime = performance.now()
        const response = await axios.get('/api/warmup', { timeout: 30000 }) // 30s timeout for cold starts
        const endTime = performance.now()
        
        console.log('✅ Server warmup completed:', {
          status: response.data.status,
          warmupTime: response.data.warmup_time_ms,
          totalTime: Math.round(endTime - startTime),
          modelsLoaded: response.data.models_loaded
        })
        
        setServerWarmedUp(true)
        setWarmupStatus('ready')
      } catch (err) {
        console.warn('⚠️ Server warmup failed (non-critical):', err.message)
        // Don't show error to user - this is a background optimization
        setServerWarmedUp(true) // Mark as warmed up anyway to prevent blocking
        setWarmupStatus('error')
      }
    }

    warmupServer()
  }, []) // Run once on mount

  // Keep-alive: Ping server every 2 minutes to prevent worker sleep
  useEffect(() => {
    if (!serverWarmedUp) return

    const keepAlive = setInterval(async () => {
      try {
        await axios.get('/api/health', { timeout: 5000 })
        console.log('🔄 Keep-alive ping successful')
      } catch (err) {
        console.warn('⚠️ Keep-alive ping failed:', err.message)
      }
    }, 120000) // Every 2 minutes

    return () => clearInterval(keepAlive)
  }, [serverWarmedUp])

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
      if (payload.user_id) setSearchSuccessWithUserId(payload.user_id)
      
      // Trigger profile refresh
      setRefreshTrigger(prev => prev + 1)

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
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between gap-2">
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent mb-0.5">
                Gravity
              </h1>
              <p className="text-muted-foreground text-sm">High-Performance Ad Retrieval System</p>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex gap-1.5">
                <Badge variant="secondary" className="flex items-center gap-1 px-2 py-0.5 text-[11px]">
                  <Database className="w-3 h-3" />
                  10k
                </Badge>
                <Badge variant="secondary" className="flex items-center gap-1 px-2 py-0.5 text-[11px]">
                  <Target className="w-3 h-3" />
                  &lt;100ms
                </Badge>
                <Badge variant="secondary" className="flex items-center gap-1 px-2 py-0.5 text-[11px]">
                  <Zap className="w-3 h-3" />
                  384D
                </Badge>
                {warmupStatus === 'warming' && (
                  <Badge variant="outline" className="flex items-center gap-1 px-2 py-0.5 text-[11px] animate-pulse">
                    <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                    Warming...
                  </Badge>
                )}
                {warmupStatus === 'ready' && (
                  <Badge variant="outline" className="flex items-center gap-1 px-2 py-0.5 text-[11px]">
                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                    Ready
                  </Badge>
                )}
              </div>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 py-4 px-4">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-[1fr_300px] gap-4">
          <div className="space-y-4 min-w-0">
            <div className="animate-slide-down">
              <UserSummaryPanel
                onSelectUser={setSelectedUserIdForSearch}
                searchSuccessWithUserId={searchSuccessWithUserId}
                refreshTrigger={refreshTrigger}
              />
            </div>

            <Card className="animate-slide-down shadow-md">
              <div className="p-4">
                <h2 className="text-lg font-semibold mb-3 text-foreground">Search Query</h2>
                <QueryInput onSubmit={handleSearch} loading={loading} />
              </div>
            </Card>

            {error && (
              <Card className="border-destructive/50 bg-destructive/10 animate-slide-down">
                <div className="p-3">
                  <p className="text-destructive text-sm font-medium"><strong>Error:</strong> {error}</p>
                </div>
              </Card>
            )}

            <div className="animate-slide-up">
              <h2 className="text-lg font-semibold mb-3 text-foreground px-0.5">
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

          <aside className="lg:sticky lg:top-20 h-fit space-y-3">
            <div className="animate-fade-in">
              <MetricsPanel 
                metrics={results?.metadata} 
                latency={latency}
              />
            </div>
          </aside>
        </div>
      </main>

      <footer className="border-t border-border bg-card text-muted-foreground py-3 px-4 text-center text-xs">
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

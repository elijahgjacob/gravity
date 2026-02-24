import React, { useState } from 'react'
import axios from 'axios'
import QueryInput from './components/QueryInput'
import ResultsDisplay from './components/ResultsDisplay'
import MetricsPanel from './components/MetricsPanel'
import RequestResponseViewer from './components/RequestResponseViewer'
import UserSummaryPanel from './components/UserSummaryPanel'

function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [latency, setLatency] = useState(null)
  const [lastRequest, setLastRequest] = useState(null)
  const [lastResponse, setLastResponse] = useState(null)

  const handleSearch = async (requestData) => {
    setLoading(true)
    setError(null)
    setLastRequest(requestData)
    
    const startTime = performance.now()
    
    try {
      const response = await axios.post('/api/retrieve', requestData)
      const endTime = performance.now()
      
      setResults(response.data)
      setLatency(response.data.latency_ms)
      setLastResponse(response.data)
      
      console.log('Search completed:', {
        query: requestData.query,
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
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1>Gravity</h1>
          <p className="subtitle">High-Performance Ad Retrieval System</p>
          <div className="header-stats">
            <span className="stat">10,000 Campaigns</span>
            <span className="stat-divider">•</span>
            <span className="stat">Target: &lt; 100ms p95</span>
            <span className="stat-divider">•</span>
            <span className="stat">384D Vector Search</span>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="content-wrapper">
          <div className="main-content">
            <UserSummaryPanel />
            <section className="query-section">
              <h2>Search Query</h2>
              <QueryInput onSubmit={handleSearch} loading={loading} />
            </section>

            {error && (
              <div className="error-message">
                <strong>Error:</strong> {error}
              </div>
            )}

            <section className="results-section">
              <h2>
                {results ? `Results (${results.campaigns.length} campaigns)` : 'Results'}
              </h2>
              <ResultsDisplay results={results} />
            </section>

            <section className="debug-section">
              <RequestResponseViewer 
                request={lastRequest}
                response={lastResponse}
              />
            </section>
          </div>

          <aside className="sidebar">
            <MetricsPanel 
              metrics={results?.metadata} 
              latency={latency}
            />
          </aside>
        </div>
      </main>

      <footer className="app-footer">
        <p>
          Powered by FastAPI + React | 
          <a href="/api/docs" target="_blank" rel="noopener noreferrer"> API Docs</a> | 
          <a href="https://github.com/elijahgjacob/gravity" target="_blank" rel="noopener noreferrer"> GitHub</a>
        </p>
      </footer>
    </div>
  )
}

export default App

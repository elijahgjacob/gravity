import React from 'react'

export default function MetricsPanel({ metrics, latency }) {
  if (!metrics && !latency) {
    return (
      <div className="metrics-panel">
        <h3>Performance Metrics</h3>
        <p className="metrics-placeholder">Metrics will appear after your first search</p>
      </div>
    )
  }

  const getLatencyColor = (ms) => {
    if (ms < 50) return 'excellent'
    if (ms < 100) return 'good'
    if (ms < 200) return 'fair'
    return 'slow'
  }

  const formatLatency = (ms) => {
    return ms ? `${ms.toFixed(2)}ms` : 'N/A'
  }

  return (
    <div className="metrics-panel">
      <h3>Performance Metrics</h3>
      
      <div className="metric-card primary">
        <div className="metric-label">Total Latency</div>
        <div className={`metric-value ${getLatencyColor(latency)}`}>
          {formatLatency(latency)}
        </div>
        <div className="metric-target">Target: &lt; 100ms</div>
      </div>

      {metrics && (
        <>
          <div className="metric-breakdown">
            <h4>Breakdown</h4>
            {metrics.short_circuited ? (
              <div className="short-circuit-info">
                <p className="info-text">Request short-circuited</p>
                <p className="reason">{metrics.reason}</p>
              </div>
            ) : (
              <div className="breakdown-items">
                <div className="breakdown-item">
                  <span className="breakdown-label">Eligibility Check</span>
                  <span className="breakdown-value">~8ms</span>
                </div>
                <div className="breakdown-item">
                  <span className="breakdown-label">Category Extraction</span>
                  <span className="breakdown-value">~5ms</span>
                </div>
                <div className="breakdown-item">
                  <span className="breakdown-label">Query Embedding</span>
                  <span className="breakdown-value">~7ms</span>
                </div>
                <div className="breakdown-item">
                  <span className="breakdown-label">Vector Search</span>
                  <span className="breakdown-value">~2ms</span>
                </div>
                <div className="breakdown-item">
                  <span className="breakdown-label">Relevance Ranking</span>
                  <span className="breakdown-value">~1ms</span>
                </div>
              </div>
            )}
          </div>

          <div className="metric-info">
            <h4>Request Info</h4>
            <div className="info-item">
              <span className="info-label">Campaigns Returned</span>
              <span className="info-value">{metrics.campaigns_count || 0}</span>
            </div>
            {metrics.short_circuited && (
              <div className="info-item">
                <span className="info-label">Short-circuited</span>
                <span className="info-value">Yes</span>
              </div>
            )}
          </div>
        </>
      )}

      <div className="performance-legend">
        <h4>Performance Guide</h4>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-dot excellent"></span>
            <span>&lt; 50ms: Excellent</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot good"></span>
            <span>50-100ms: Good</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot fair"></span>
            <span>100-200ms: Fair</span>
          </div>
          <div className="legend-item">
            <span className="legend-dot slow"></span>
            <span>&gt; 200ms: Slow</span>
          </div>
        </div>
      </div>
    </div>
  )
}

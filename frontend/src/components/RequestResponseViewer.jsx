import React, { useState } from 'react'

export default function RequestResponseViewer({ request, response }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [activeTab, setActiveTab] = useState('request')

  if (!request && !response) {
    return null
  }

  return (
    <div className="req-res-viewer">
      <button
        className="viewer-toggle"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? '− Hide' : '+ Show'} Request/Response
      </button>

      {isExpanded && (
        <div className="viewer-content">
          <div className="viewer-tabs">
            <button
              className={`tab ${activeTab === 'request' ? 'active' : ''}`}
              onClick={() => setActiveTab('request')}
            >
              Request
            </button>
            <button
              className={`tab ${activeTab === 'response' ? 'active' : ''}`}
              onClick={() => setActiveTab('response')}
            >
              Response
            </button>
          </div>

          <div className="viewer-body">
            {activeTab === 'request' && request && (
              <pre className="json-content">
                {JSON.stringify(request, null, 2)}
              </pre>
            )}
            {activeTab === 'response' && response && (
              <pre className="json-content">
                {JSON.stringify(response, null, 2)}
              </pre>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

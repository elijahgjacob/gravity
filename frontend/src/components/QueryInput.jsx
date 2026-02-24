import React, { useState } from 'react'

export default function QueryInput({ onSubmit, loading }) {
  const [query, setQuery] = useState('')
  const [showContext, setShowContext] = useState(false)
  const [context, setContext] = useState({
    age: '',
    gender: '',
    location: '',
    interests: ''
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!query.trim()) return

    const requestData = { query: query.trim() }
    
    if (showContext && (context.age || context.gender || context.location || context.interests)) {
      requestData.context = {}
      if (context.age) requestData.context.age = parseInt(context.age)
      if (context.gender) requestData.context.gender = context.gender
      if (context.location) requestData.context.location = context.location
      if (context.interests) requestData.context.interests = context.interests.split(',').map(i => i.trim())
    }

    onSubmit(requestData)
  }

  const exampleQueries = [
    'best running shoes for marathon',
    'affordable laptop for students',
    'luxury watches for men',
    'organic dog food delivery',
    'yoga classes near me'
  ]

  return (
    <div className="query-input-container">
      <form onSubmit={handleSubmit}>
        <div className="query-section">
          <label htmlFor="query">Search Query</label>
          <input
            id="query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter a search query..."
            disabled={loading}
            className="query-input"
          />
          
          <div className="example-queries">
            <span>Examples:</span>
            {exampleQueries.map((example, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setQuery(example)}
                disabled={loading}
                className="example-btn"
              >
                {example}
              </button>
            ))}
          </div>
        </div>

        <div className="context-section">
          <button
            type="button"
            onClick={() => setShowContext(!showContext)}
            className="toggle-context-btn"
            disabled={loading}
          >
            {showContext ? '− Hide' : '+ Add'} Context (Optional)
          </button>

          {showContext && (
            <div className="context-fields">
              <div className="context-row">
                <div className="field">
                  <label htmlFor="age">Age</label>
                  <input
                    id="age"
                    type="number"
                    value={context.age}
                    onChange={(e) => setContext({...context, age: e.target.value})}
                    placeholder="e.g., 25"
                    disabled={loading}
                  />
                </div>
                <div className="field">
                  <label htmlFor="gender">Gender</label>
                  <select
                    id="gender"
                    value={context.gender}
                    onChange={(e) => setContext({...context, gender: e.target.value})}
                    disabled={loading}
                  >
                    <option value="">Select...</option>
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
              <div className="context-row">
                <div className="field">
                  <label htmlFor="location">Location</label>
                  <input
                    id="location"
                    type="text"
                    value={context.location}
                    onChange={(e) => setContext({...context, location: e.target.value})}
                    placeholder="e.g., New York"
                    disabled={loading}
                  />
                </div>
                <div className="field">
                  <label htmlFor="interests">Interests</label>
                  <input
                    id="interests"
                    type="text"
                    value={context.interests}
                    onChange={(e) => setContext({...context, interests: e.target.value})}
                    placeholder="e.g., sports, technology"
                    disabled={loading}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        <button type="submit" disabled={loading || !query.trim()} className="submit-btn">
          {loading ? 'Searching...' : 'Search Campaigns'}
        </button>
      </form>
    </div>
  )
}

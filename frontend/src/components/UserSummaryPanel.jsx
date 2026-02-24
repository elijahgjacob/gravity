import React, { useState, useEffect, useCallback } from 'react'
import axios from 'axios'

export default function UserSummaryPanel() {
  const [userIds, setUserIds] = useState([])
  const [usersLoading, setUsersLoading] = useState(true)
  const [usersError, setUsersError] = useState(null)
  const [selectedUserId, setSelectedUserId] = useState('')
  const [profile, setProfile] = useState(null)
  const [summary, setSummary] = useState(null)
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [summaryError, setSummaryError] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)

  const fetchUsers = useCallback(async () => {
    setUsersLoading(true)
    setUsersError(null)
    try {
      const res = await axios.get('/api/analytics/users')
      setUserIds(res.data.user_ids || [])
      if (!res.data.user_ids?.length) setSelectedUserId('')
    } catch (err) {
      setUsersError(err.response?.data?.detail || err.message || 'Failed to load users')
      setUserIds([])
      setSelectedUserId('')
    } finally {
      setUsersLoading(false)
    }
  }, [])

  const fetchProfileSummary = useCallback(async (userId, analyze = false) => {
    if (!userId) {
      setProfile(null)
      setSummary(null)
      setSummaryError(null)
      return
    }
    setSummaryLoading(true)
    setSummaryError(null)
    try {
      const url = `/api/analytics/profile/${encodeURIComponent(userId)}/summary${analyze ? '?analyze=true' : ''}`
      const res = await axios.get(url)
      setProfile(res.data.profile || null)
      setSummary(res.data.summary || null)
    } catch (err) {
      if (err.response?.status === 404) {
        setSummaryError(`User ${userId} not found`)
      } else if (err.response?.status === 503) {
        setSummaryError('Profile or summary service not available')
      } else {
        setSummaryError(err.response?.data?.detail || err.message || 'Failed to load profile')
      }
      setProfile(null)
      setSummary(null)
    } finally {
      setSummaryLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  useEffect(() => {
    if (selectedUserId) {
      fetchProfileSummary(selectedUserId)
    } else {
      setProfile(null)
      setSummary(null)
      setSummaryError(null)
    }
  }, [selectedUserId, fetchProfileSummary])

  const handleRefreshAnalysis = async () => {
    if (!selectedUserId) return
    setAnalyzing(true)
    setSummaryError(null)
    try {
      await axios.post(`/api/analytics/profile/${encodeURIComponent(selectedUserId)}/analyze`)
      await fetchProfileSummary(selectedUserId, true)
    } catch (err) {
      setSummaryError(err.response?.data?.detail || err.message || 'Analysis failed')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <section className="user-summary-section">
      <h2>User Summary</h2>

      <div className="user-select-row">
        <label htmlFor="user-select">User</label>
        <select
          id="user-select"
          value={selectedUserId}
          onChange={(e) => setSelectedUserId(e.target.value)}
          disabled={usersLoading}
          className="user-summary-select"
          aria-label="Select user"
        >
          <option value="">-- Select a user --</option>
          {userIds.length === 0 && !usersLoading && <option value="" disabled>No users in cache</option>}
          {userIds.map((id) => (
            <option key={id} value={id}>{id}</option>
          ))}
        </select>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={handleRefreshAnalysis}
          disabled={!selectedUserId || summaryLoading || analyzing}
        >
          {analyzing ? 'Analyzing...' : 'Refresh analysis'}
        </button>
      </div>

      {usersError && (
        <div className="user-summary-error">{usersError}</div>
      )}

      {!selectedUserId && !usersError && (
        <p className="user-summary-placeholder">Select a user to view their profile and LLM summary.</p>
      )}

      {selectedUserId && summaryError && (
        <div className="user-summary-error">{summaryError}</div>
      )}

      {selectedUserId && summaryLoading && !profile && (
        <p className="user-summary-placeholder">Loading profile and summary...</p>
      )}

      {selectedUserId && profile && (
        <div className="user-summary-panel">
          <div className="summary-meta-row">
            <span className="user-id-badge">{profile.user_id}</span>
            <span>Queries: {profile.query_count ?? 0}</span>
            <span>Updated: {profile.last_updated ? new Date(profile.last_updated).toLocaleString() : '—'}</span>
          </div>

          {profile.query_history?.length > 0 && (
            <div className="summary-block">
              <h3>Recent queries</h3>
              <ol className="summary-query-list">
                {profile.query_history.slice(-15).reverse().map((item, idx) => (
                  <li key={idx}>{item.query}</li>
                ))}
              </ol>
            </div>
          )}

          {profile.inferred_intents?.length > 0 && (
            <div className="summary-block">
              <h3>Inferred intents</h3>
              <ul className="summary-intents-list">
                {profile.inferred_intents.map((intent, idx) => (
                  <li key={idx}>
                    <strong>{intent.intent_type}</strong>
                    {' '}({(intent.confidence * 100).toFixed(0)}%)
                    {intent.metadata && Object.keys(intent.metadata).length > 0 && (
                      <> · {JSON.stringify(intent.metadata)}</>
                    )}
                    {intent.inferred_categories?.length > 0 && (
                      <> · Categories: {intent.inferred_categories.join(', ')}</>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {(profile.inferred_categories?.length > 0 || profile.aggregated_interests?.length > 0) && (
            <div className="summary-block">
              <h3>Categories &amp; interests</h3>
              <div className="summary-tags">
                {(profile.inferred_categories || []).map((cat) => (
                  <span key={cat} className="category-tag">{cat}</span>
                ))}
                {(profile.aggregated_interests || []).map((interest) => (
                  <span key={interest} className="category-tag summary-interest">{interest}</span>
                ))}
              </div>
            </div>
          )}

          <div className="summary-block">
            <h3>LLM Summary</h3>
            {summary ? (
              <>
                <div className="summary-narrative">{summary.narrative_summary}</div>
                {summary.suggested_campaigns?.length > 0 && (
                  <>
                    <h4 className="summary-campaigns-title">Suggested ad campaigns</h4>
                    <ul className="suggested-campaigns-list">
                      {summary.suggested_campaigns.map((campaign, idx) => (
                        <li key={idx}>{campaign}</li>
                      ))}
                    </ul>
                  </>
                )}
              </>
            ) : (
              <p className="user-summary-placeholder">Summary not available (LLM may be disabled or key not set).</p>
            )}
          </div>
        </div>
      )}
    </section>
  )
}

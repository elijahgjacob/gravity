import React, { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Label } from './ui/label'
import { Select } from './ui/select'
import { Badge } from './ui/badge'
import { User, RefreshCw, Loader2, TrendingUp, Tag } from 'lucide-react'

/** Sanitize for use in user_id: keep alphanumeric, dots, hyphens; collapse underscores; limit length */
function sanitizeIdPart(s) {
  if (typeof s !== 'string' || !s.trim()) return ''
  return s.trim()
    .replace(/[^a-zA-Z0-9.-]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '')
    .slice(0, 64)
}

/** Derive a stable user_id from IP address and device ID (for labeling/identifying users) */
function deriveUserId(ip, deviceId) {
  const ipPart = sanitizeIdPart(ip)
  const devPart = sanitizeIdPart(deviceId)
  if (!ipPart && !devPart) return ''
  const parts = []
  if (ipPart) parts.push('ip', ipPart)
  if (devPart) parts.push('dev', devPart)
  return parts.join('_') || ''
}

export default function UserSummaryPanel({ onSelectUser }) {
  const [ipAddress, setIpAddress] = useState('')
  const [deviceId, setDeviceId] = useState('')
  const [userIds, setUserIds] = useState([])
  const [usersLoading, setUsersLoading] = useState(true)
  const [usersError, setUsersError] = useState(null)
  const [userIdInput, setUserIdInput] = useState('')  // manual demo input
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
    } catch (err) {
      setUsersError(err.response?.data?.detail || err.message || 'Failed to load users')
      setUserIds([])
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

  useEffect(() => {
    if (typeof onSelectUser === 'function') onSelectUser(selectedUserId || null)
  }, [selectedUserId, onSelectUser])

  const handleUseIdentityUser = () => {
    const id = deriveUserId(ipAddress, deviceId)
    if (!id) return
    setUserIdInput(id)
    setSelectedUserId(id)
  }

  const handleLoadUser = () => {
    const id = userIdInput.trim()
    if (id) setSelectedUserId(id)
  }

  const handleCacheSelect = (e) => {
    const id = e.target.value
    setUserIdInput(id)
    setSelectedUserId(id)
  }

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
    <Card className="shadow-md bg-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-2xl">
          <User className="w-6 h-6" />
          User Summary
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-5">
        <div className="p-4 bg-muted rounded-lg border border-border space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-1">Identify user (IP + device)</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Set IP and device ID to label this user. Use this user, then run a search to create or update their profile.
            </p>
          </div>

          <div className="flex flex-wrap gap-3 items-end">
            <div className="flex-1 min-w-[140px] space-y-1.5">
              <Label htmlFor="ip-address" className="text-xs">IP address</Label>
              <Input
                id="ip-address"
                type="text"
                value={ipAddress}
                onChange={(e) => setIpAddress(e.target.value)}
                placeholder="e.g. 192.168.1.1"
                className="font-mono text-sm h-9"
                aria-label="IP address"
              />
            </div>
            <div className="flex-1 min-w-[140px] space-y-1.5">
              <Label htmlFor="device-id" className="text-xs">Device ID</Label>
              <Input
                id="device-id"
                type="text"
                value={deviceId}
                onChange={(e) => setDeviceId(e.target.value)}
                placeholder="e.g. device_abc123"
                className="font-mono text-sm h-9"
                aria-label="Device ID"
              />
            </div>
            <Button
              type="button"
              onClick={handleUseIdentityUser}
              disabled={(!ipAddress.trim() && !deviceId.trim()) || summaryLoading}
              size="sm"
              className="h-9"
            >
              Use this user
            </Button>
          </div>

          {deriveUserId(ipAddress, deviceId) && (
            <div className="pt-2">
              <p className="text-xs text-muted-foreground">
                Derived ID: <code className="bg-muted-foreground/20 px-2 py-0.5 rounded text-foreground font-mono">
                  {deriveUserId(ipAddress, deviceId)}
                </code>
              </p>
            </div>
          )}
        </div>

        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[180px] space-y-1.5">
            <Label htmlFor="user-id-input" className="text-sm font-semibold">User ID (demo)</Label>
            <Input
              id="user-id-input"
              type="text"
              value={userIdInput}
              onChange={(e) => setUserIdInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleLoadUser()}
              placeholder="e.g. 192.233.24 or user_123"
              className="font-mono text-sm"
              aria-label="User ID for demo"
            />
          </div>
          <Button
            type="button"
            onClick={handleLoadUser}
            disabled={!userIdInput.trim() || summaryLoading}
          >
            Load
          </Button>
        </div>

        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[200px] space-y-1.5">
            <Label htmlFor="user-select" className="text-sm font-semibold">From cache</Label>
            <Select
              id="user-select"
              value={userIds.includes(selectedUserId) ? selectedUserId : ''}
              onChange={handleCacheSelect}
              disabled={usersLoading}
              className="font-mono text-sm"
              aria-label="Select cached user"
            >
              <option value="">-- Pick a cached user --</option>
              {userIds.length === 0 && !usersLoading && <option value="" disabled>No users in cache</option>}
              {userIds.map((id) => (
                <option key={id} value={id}>{id}</option>
              ))}
            </Select>
          </div>
          <Button
            type="button"
            onClick={handleRefreshAnalysis}
            disabled={!selectedUserId || summaryLoading || analyzing}
            variant="outline"
          >
            {analyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                Refresh analysis
              </>
            )}
          </Button>
        </div>

        {usersError && (
          <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-destructive text-sm">
            {usersError}
          </div>
        )}

        {!selectedUserId && !usersError && (
          <p className="text-sm text-muted-foreground italic py-2">
            Select a user to view their profile and LLM summary.
          </p>
        )}

        {selectedUserId && summaryError && (
          <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-destructive text-sm">
            {summaryError}
          </div>
        )}

        {selectedUserId && summaryLoading && !profile && (
          <div className="flex items-center gap-2 py-4 text-muted-foreground">
            <Loader2 className="w-4 h-4 animate-spin" />
            <p className="text-sm">Loading profile and summary...</p>
          </div>
        )}

        {selectedUserId && profile && (
          <div className="space-y-5 pt-4 border-t border-border">
            <div className="flex flex-wrap gap-2 items-center text-sm">
              <Badge className="font-mono">
                {profile.user_id}
              </Badge>
              <Badge variant="secondary" className="bg-blue-600/20 text-blue-400 border-blue-500/30">
                {profile.query_count ?? 0} queries
              </Badge>
              <span className="text-xs text-muted-foreground">
                Updated: {profile.last_updated ? new Date(profile.last_updated).toLocaleString() : '—'}
              </span>
            </div>

            {profile.query_history?.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Recent queries
                </h3>
                <div className="p-3 bg-muted rounded-lg border border-border max-h-48 overflow-y-auto">
                  <ol className="space-y-1 text-sm list-decimal list-inside">
                    {profile.query_history.slice(-15).reverse().map((item, idx) => (
                      <li key={idx} className="text-foreground">{item.query}</li>
                    ))}
                  </ol>
                </div>
              </div>
            )}

            {profile.inferred_intents?.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-foreground">Inferred intents</h3>
                <ul className="space-y-2">
                  {profile.inferred_intents.map((intent, idx) => (
                    <li key={idx} className="text-sm p-2 bg-muted rounded border border-border">
                      <span className="font-semibold text-foreground">{intent.intent_type}</span>
                      <Badge variant="outline" className="ml-2 text-xs">
                        {(intent.confidence * 100).toFixed(0)}%
                      </Badge>
                      {intent.metadata && Object.keys(intent.metadata).length > 0 && (
                        <span className="text-muted-foreground"> · {JSON.stringify(intent.metadata)}</span>
                      )}
                      {intent.inferred_categories?.length > 0 && (
                        <span className="text-muted-foreground"> · Categories: {intent.inferred_categories.join(', ')}</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {(profile.inferred_categories?.length > 0 || profile.aggregated_interests?.length > 0) && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                  <Tag className="w-4 h-4" />
                  Categories &amp; interests
                </h3>
                <div className="flex flex-wrap gap-2">
                  {(profile.inferred_categories || []).map((cat) => (
                    <Badge key={cat} variant="secondary" className="bg-purple-600/20 text-purple-400 border-purple-500/30">
                      {cat}
                    </Badge>
                  ))}
                  {(profile.aggregated_interests || []).map((interest) => (
                    <Badge key={interest} variant="secondary" className="bg-indigo-600/20 text-indigo-400 border-indigo-500/30">
                      {interest}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-foreground">LLM Summary</h3>
              {summary ? (
                <div className="space-y-3">
                  <div className="p-4 bg-gradient-to-br from-blue-600/10 to-indigo-600/10 rounded-lg border-l-4 border-blue-500">
                    <p className="text-sm text-foreground leading-relaxed">{summary.narrative_summary}</p>
                  </div>
                  {summary.suggested_campaigns?.length > 0 && (
                    <>
                      <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                        Suggested ad campaigns
                      </h4>
                      <ul className="space-y-1.5">
                        {summary.suggested_campaigns.map((campaign, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-sm text-foreground">
                            <span className="text-blue-500 font-bold mt-0.5">→</span>
                            <span>{campaign}</span>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground italic py-2">
                  Summary not available (LLM may be disabled or key not set).
                </p>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

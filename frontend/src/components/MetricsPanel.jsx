import React from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card'
import { Badge } from './ui/badge'
import { Clock, Activity, Zap, CheckCircle2, XCircle } from 'lucide-react'

export default function MetricsPanel({ metrics, latency }) {
  if (!metrics && !latency) {
    return (
      <Card className="shadow-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl">
            <Activity className="w-5 h-5" />
            Performance Metrics
          </CardTitle>
          <CardDescription className="text-muted-foreground">
            Metrics will appear after your first search
          </CardDescription>
        </CardHeader>
      </Card>
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
    <Card className="shadow-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <Activity className="w-5 h-5" />
          Performance Metrics
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-5">
        <div className="p-5 bg-gradient-to-br from-primary to-primary/80 rounded-lg text-primary-foreground shadow-lg">
          <div className="flex items-center gap-2 mb-2 opacity-90">
            <Clock className="w-4 h-4" />
            <span className="text-sm font-medium">Total Latency</span>
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`text-4xl font-bold ${
              latency < 50 ? 'text-emerald-300' :
              latency < 100 ? 'text-blue-300' :
              latency < 200 ? 'text-amber-300' :
              'text-red-300'
            }`}>
              {formatLatency(latency)}
            </span>
          </div>
          <p className="text-xs opacity-75 mt-2">Target: &lt; 100ms</p>
        </div>

        {metrics && (
          <>
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Breakdown
              </h4>
              {metrics.short_circuited ? (
                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <XCircle className="w-4 h-4 text-amber-500" />
                    <p className="text-sm font-semibold text-amber-500">Request short-circuited</p>
                  </div>
                  <p className="text-xs text-amber-400/80">{metrics.reason}</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {[
                    { label: 'Eligibility Check', value: '~8ms' },
                    { label: 'Category Extraction', value: '~5ms' },
                    { label: 'Query Embedding', value: '~7ms' },
                    { label: 'Vector Search', value: '~2ms' },
                    { label: 'Relevance Ranking', value: '~1ms' }
                  ].map((item, idx) => (
                    <div key={idx} className="flex justify-between items-center text-sm py-1.5 px-2 rounded hover:bg-muted transition-colors">
                      <span className="text-muted-foreground">{item.label}</span>
                      <span className="font-semibold text-foreground">{item.value}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-4 border-t border-border space-y-2">
              <h4 className="text-sm font-semibold text-foreground">Request Info</h4>
              <div className="flex justify-between items-center text-sm py-1.5">
                <span className="text-muted-foreground">Campaigns Returned</span>
                <Badge variant="secondary">
                  {metrics.campaigns_count || 0}
                </Badge>
              </div>
              {metrics.short_circuited && (
                <div className="flex justify-between items-center text-sm py-1.5">
                  <span className="text-muted-foreground">Short-circuited</span>
                  <Badge variant="secondary" className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                    Yes
                  </Badge>
                </div>
              )}
            </div>
          </>
        )}

        <div className="pt-4 border-t border-border space-y-2">
          <h4 className="text-sm font-semibold text-foreground">Performance Guide</h4>
          <div className="space-y-1.5">
            {[
              { color: 'bg-emerald-500', label: '< 50ms: Excellent' },
              { color: 'bg-blue-500', label: '50-100ms: Good' },
              { color: 'bg-amber-500', label: '100-200ms: Fair' },
              { color: 'bg-red-500', label: '> 200ms: Slow' }
            ].map((item, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs text-muted-foreground">
                <div className={`w-3 h-3 rounded-full ${item.color}`}></div>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

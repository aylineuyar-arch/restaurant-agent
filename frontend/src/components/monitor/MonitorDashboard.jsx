import { useState, useEffect, useCallback } from 'react'

// ── Helpers ───────────────────────────────────────────────────────────────────
function relTime(iso) {
  if (!iso) return '—'
  const diff = Date.now() - new Date(iso).getTime()
  const s = Math.floor(diff / 1000)
  if (s < 60)  return `${s}s ago`
  if (s < 3600) return `${Math.floor(s / 60)}m ago`
  return `${Math.floor(s / 3600)}h ago`
}

function ms(val) {
  if (!val) return '—'
  return val >= 1000 ? `${(val / 1000).toFixed(1)}s` : `${val}ms`
}

function confColor(score) {
  if (score >= 0.8) return 'text-emerald-400'
  if (score >= 0.5) return 'text-yellow-400'
  return 'text-red-400'
}

const NODE_LABELS = {
  parse_input:    { label: 'Parse',    model: 'Haiku'   },
  check_memory:   { label: 'Memory',   model: 'ChromaDB' },
  research:       { label: 'Research', model: 'Tavily'  },
  retry_research: { label: 'Retry',    model: 'Tavily'  },
  enrich:         { label: 'Enrich',   model: 'Tavily'  },
  rank:           { label: 'Rank',     model: 'Sonnet'  },
  book:           { label: 'Book',     model: 'LangGraph'},
  save:           { label: 'Save',     model: 'ChromaDB' },
  send_email:     { label: 'Email',    model: 'Resend'  },
}

// ── Stats Row ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, sub }) {
  return (
    <div className="bg-surface border border-subtle rounded-xl px-5 py-4">
      <p className="text-xs text-muted uppercase tracking-widest mb-1">{label}</p>
      <p className="text-2xl font-bold text-ink font-display">{value}</p>
      {sub && <p className="text-xs text-muted mt-0.5">{sub}</p>}
    </div>
  )
}

// ── Node Timeline ─────────────────────────────────────────────────────────────
function NodeTimeline({ traces, totalMs }) {
  const total = totalMs || traces.reduce((s, t) => s + t.latency_ms, 0) || 1
  return (
    <div className="space-y-2 mt-4">
      {traces.map((t, i) => {
        const info  = NODE_LABELS[t.node_name] || { label: t.node_name, model: '' }
        const pct   = Math.max(2, Math.round((t.latency_ms / total) * 100))
        const color = t.status === 'error' ? 'bg-red-500/70' :
                      t.node_name === 'retry_research' ? 'bg-yellow-500/70' : 'bg-accent/70'
        return (
          <div key={i} className="flex items-center gap-3">
            <div className="w-20 shrink-0 text-right">
              <span className="text-xs text-muted">{info.label}</span>
            </div>
            <div className="flex-1 bg-white/5 rounded-full h-4 relative overflow-hidden">
              <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${pct}%` }} />
            </div>
            <div className="w-16 shrink-0">
              <span className="text-xs text-muted">{ms(t.latency_ms)}</span>
            </div>
            <div className="w-16 shrink-0">
              <span className={`text-xs ${t.status === 'error' ? 'text-red-400' : 'text-emerald-400/60'}`}>
                {t.status}
              </span>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── Run Detail Panel ──────────────────────────────────────────────────────────
function RunDetail({ run, onClose }) {
  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0F0E0B] border border-subtle rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-7">
        <div className="flex items-start justify-between mb-6">
          <div>
            <p className="text-xs text-muted uppercase tracking-widest mb-1">Workflow trace</p>
            <h3 className="font-display text-lg text-ink leading-snug max-w-lg">
              "{run.query}"
            </h3>
          </div>
          <button onClick={onClose} className="text-muted hover:text-ink text-xl ml-4 shrink-0">×</button>
        </div>

        {/* Meta */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          {[
            ['Status',       run.status],
            ['Total time',   ms(run.total_latency_ms)],
            ['Recs',         run.recommendations_count ?? '—'],
            ['Confidence',   run.confidence_score?.toFixed(2) ?? '—'],
            ['AI eval',      run.eval_score != null ? run.eval_score.toFixed(2) : '—'],
            ['Escalated',    run.escalated ? 'yes' : 'no'],
          ].map(([k, v]) => (
            <div key={k} className="bg-surface border border-subtle rounded-xl px-4 py-3">
              <p className="text-xs text-muted mb-0.5">{k}</p>
              <p className={`text-sm font-semibold ${
                k === 'Escalated' && run.escalated ? 'text-red-400' :
                k === 'Confidence' ? confColor(run.confidence_score) : 'text-ink'
              }`}>{v}</p>
            </div>
          ))}
        </div>

        {/* Node timeline */}
        <div>
          <p className="text-xs text-muted uppercase tracking-widest mb-3">Node pipeline</p>
          {run.traces?.length > 0
            ? <NodeTimeline traces={run.traces} totalMs={run.total_latency_ms} />
            : <p className="text-muted text-sm">No trace data</p>
          }
        </div>

        {/* User feedback */}
        {run.feedback?.length > 0 && (
          <div className="mt-6">
            <p className="text-xs text-muted uppercase tracking-widest mb-3">User feedback</p>
            <div className="space-y-1.5">
              {run.feedback.map((f, i) => (
                <div key={i} className="flex items-center gap-3 text-sm">
                  <span>{f.rating === 1 ? '👍' : '👎'}</span>
                  <span className="text-ink">{f.restaurant}</span>
                  <span className="text-muted text-xs">{relTime(f.created_at)}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Run ID */}
        <p className="text-xs text-white/15 mt-6 font-mono">{run.run_id}</p>
      </div>
    </div>
  )
}

// ── Runs Table ────────────────────────────────────────────────────────────────
function RunsTable({ runs, onSelect }) {
  if (!runs.length) {
    return <p className="text-muted text-sm text-center py-8">no runs yet — run a search first</p>
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-xs text-muted uppercase tracking-widest border-b border-subtle">
            {['Query', 'Status', 'Latency', 'Recs', 'Confidence', 'AI Eval', 'Time'].map(h => (
              <th key={h} className="text-left pb-3 pr-4 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {runs.map(run => (
            <tr
              key={run.run_id}
              onClick={() => onSelect(run)}
              className="hover:bg-white/3 cursor-pointer transition-colors"
            >
              <td className="py-3 pr-4 text-ink max-w-[200px] truncate">
                {run.escalated ? <span className="text-red-400 mr-1.5">⚠</span> : null}
                {run.query}
              </td>
              <td className="py-3 pr-4">
                <span className={`text-xs px-2 py-0.5 rounded-full border ${
                  run.status === 'done'    ? 'border-emerald-500/30 text-emerald-400' :
                  run.status === 'error'   ? 'border-red-500/30 text-red-400' :
                                             'border-yellow-500/30 text-yellow-400'
                }`}>{run.status}</span>
              </td>
              <td className="py-3 pr-4 text-muted">{ms(run.total_latency_ms)}</td>
              <td className="py-3 pr-4 text-muted">{run.recommendations_count ?? '—'}</td>
              <td className={`py-3 pr-4 font-medium ${confColor(run.confidence_score)}`}>
                {run.confidence_score?.toFixed(2) ?? '—'}
              </td>
              <td className={`py-3 pr-4 font-medium ${confColor(run.eval_score)}`}>
                {run.eval_score > 0 ? run.eval_score.toFixed(2) : '—'}
              </td>
              <td className="py-3 text-muted text-xs">{relTime(run.started_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function MonitorDashboard({ apiUrl }) {
  const [stats,       setStats]       = useState(null)
  const [runs,        setRuns]        = useState([])
  const [selectedRun, setSelectedRun] = useState(null)
  const [showEscalated, setShowEscalated] = useState(false)
  const [loading,     setLoading]     = useState(true)

  const refresh = useCallback(async () => {
    try {
      const [s, r] = await Promise.all([
        fetch(`${apiUrl}/monitor/stats`).then(x => x.json()),
        fetch(`${apiUrl}/monitor/runs?limit=50&escalated_only=${showEscalated}`).then(x => x.json()),
      ])
      setStats(s)
      setRuns(r)
    } catch (e) {
      console.error('Monitor fetch error', e)
    } finally {
      setLoading(false)
    }
  }, [apiUrl, showEscalated])

  const openRun = useCallback(async (run) => {
    try {
      const detail = await fetch(`${apiUrl}/monitor/runs/${run.run_id}`).then(x => x.json())
      setSelectedRun(detail)
    } catch {
      setSelectedRun(run)
    }
  }, [apiUrl])

  useEffect(() => {
    refresh()
    const timer = setInterval(refresh, 30000)
    return () => clearInterval(timer)
  }, [refresh])

  return (
    <div className="animate-fade-in">

      {/* Stats row */}
      {loading ? (
        <div className="text-muted text-sm text-center py-16">loading…</div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-8">
            <StatCard label="Total runs"   value={stats?.total_runs ?? 0} />
            <StatCard label="Success rate" value={`${stats?.success_rate ?? 0}%`} sub={`${stats?.runs_today ?? 0} today`} />
            <StatCard label="Avg latency"  value={ms(stats?.avg_latency_ms)} />
            <StatCard label="Escalations"  value={stats?.escalated_count ?? 0} sub={`avg conf ${stats?.avg_confidence?.toFixed(2) ?? '—'}`} />
          </div>

          {/* Runs table */}
          <div className="bg-surface border border-subtle rounded-2xl p-6 mb-4">
            <div className="flex items-center justify-between mb-5">
              <p className="text-xs text-muted uppercase tracking-widest">
                {showEscalated ? 'review queue' : 'recent runs'}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => { setShowEscalated(false); refresh() }}
                  className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
                    !showEscalated ? 'bg-accent text-bg border-accent font-semibold' : 'border-subtle text-muted hover:text-ink'
                  }`}
                >
                  all runs
                </button>
                <button
                  onClick={() => { setShowEscalated(true); refresh() }}
                  className={`text-xs px-3 py-1.5 rounded-full border transition-all ${
                    showEscalated ? 'bg-red-900/60 text-red-300 border-red-500/40 font-semibold' : 'border-subtle text-muted hover:text-ink'
                  }`}
                >
                  ⚠ review queue {stats?.escalated_count > 0 ? `(${stats.escalated_count})` : ''}
                </button>
                <button
                  onClick={refresh}
                  className="text-xs text-muted hover:text-ink border border-subtle rounded-full px-3 py-1.5 transition-all"
                >
                  ↺
                </button>
              </div>
            </div>
            <RunsTable runs={runs} onSelect={openRun} />
          </div>

          <p className="text-xs text-white/15 text-center">
            est. total cost ${((stats?.avg_cost_usd ?? 0) * (stats?.total_runs ?? 0)).toFixed(3)} · auto-refreshes every 30s
          </p>
        </>
      )}

      {/* Run detail modal */}
      {selectedRun && (
        <RunDetail run={selectedRun} onClose={() => setSelectedRun(null)} />
      )}
    </div>
  )
}

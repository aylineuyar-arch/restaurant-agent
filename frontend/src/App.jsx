import { useState } from 'react'
import SearchForm from './components/SearchForm'
import AgentSteps from './components/AgentSteps'
import RestaurantCard from './components/RestaurantCard'
import MonitorDashboard from './components/monitor/MonitorDashboard'

const API_URL = import.meta.env.VITE_API_URL || `http://localhost:${import.meta.env.VITE_API_PORT || '8003'}`

export default function App() {
  const [loading, setLoading]   = useState(false)
  const [results, setResults]   = useState(null)
  const [log, setLog]           = useState([])
  const [summary, setSummary]   = useState('')
  const [error, setError]       = useState('')
  const [meta, setMeta]         = useState({})
  const [filter, setFilter]       = useState(null)
  const [lastQuery, setLastQuery] = useState('')
  const [monitor, setMonitor]     = useState(false)
  const [runId, setRunId]         = useState(null)
  const [evalVerdict, setEvalVerdict] = useState('')

  const FILTERS = [
    { key: null,         label: 'show me everything' },
    { key: 'casual',     label: 'no dress code' },
    { key: 'mid-range',  label: 'treat yourself' },
    { key: 'high-end',   label: 'full send' },
  ]

  function handleSearch(q) {
    setLoading(true)
    setError('')
    setResults(null)
    setLog([])
    setSummary('')
    setMeta({})

    setLastQuery(q)
    const url = `${API_URL}/find-restaurant-stream?q=${encodeURIComponent(q)}`
    const es  = new EventSource(url)
    let completed = false

    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)

        if (data.ping) return  // keepalive — ignore

        if (data.error) {
          setError(data.error)
          setLoading(false)
          es.close()
          return
        }

        // Live log update as each agent completes
        if (data.log?.length) {
          setLog(prev => [...prev, ...data.log])
        }

        // Final event
        if (data.done) {
          completed = true
          setResults(data.recommendations || [])
          setSummary(data.final_answer || '')
          setRunId(data.run_id || null)
          setEvalVerdict(data.eval_verdict || '')
          setMeta({
            city:       data.city,
            cuisine:    data.cuisine,
            date:       data.date,
            party_size: data.party_size,
          })
          setLoading(false)
          es.close()
        }
      } catch {
        // malformed event — ignore
      }
    }

    es.onerror = () => {
      // onerror also fires when the server closes the connection after 'done' — ignore in that case
      if (!completed) {
        setError('Connection lost — please try again')
        setLoading(false)
      }
      es.close()
    }
  }

  function handleReset() {
    setResults(null)
    setLog([])
    setSummary('')
    setError('')
    setMeta({})
    setFilter(null)
    setRunId(null)
    setEvalVerdict('')
  }

  const filtered = results
    ? (filter ? results.filter(r => (r.tags || [])[0] === filter) : results)
    : []
  const [top, ...others] = filtered

  return (
    <div className="min-h-screen bg-bg text-ink">
      {/* Top bar */}
      <header className="border-b border-subtle px-4 py-4 flex items-center justify-between">
        <span
          className="font-display text-4xl font-bold tracking-wide text-accent cursor-pointer"
          onClick={() => { setMonitor(false); handleReset() }}
        >
          fork yeah!
        </span>
        <div className="flex items-center gap-3">
          {results && !monitor && (
            <button
              onClick={handleReset}
              className="text-sm text-muted hover:text-ink border border-subtle hover:border-ink/20
                         rounded-full px-5 py-2 transition-all"
            >
              still hungry?
            </button>
          )}
          <button
            onClick={() => setMonitor(v => !v)}
            className={`text-xs border rounded-full px-4 py-2 transition-all ${
              monitor
                ? 'bg-accent/10 border-accent/40 text-accent'
                : 'border-subtle text-muted hover:text-ink hover:border-ink/20'
            }`}
          >
            {monitor ? '← back' : '⬡ monitor'}
          </button>
        </div>
      </header>

      <main className="max-w-3xl mx-auto py-8">
        {monitor && (
          <div className="px-4">
            <div className="flex items-center gap-3 mb-8">
              <p className="text-xs text-muted uppercase tracking-widest">Monitor Mode</p>
              <span className="text-xs text-white/20">— workflow observability</span>
            </div>
            <MonitorDashboard apiUrl={API_URL} />
          </div>
        )}
        {!monitor && (<>

        {/* Search — show when no results yet */}
        {!results && !loading && (
          <div className="px-4">
            <SearchForm onSearch={handleSearch} loading={loading} />
          </div>
        )}

        {/* Live agent steps — visible while loading */}
        {(loading || (log.length > 0 && !results)) && (
          <div className="px-4">
            <AgentSteps log={log} loading={loading} />
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mx-4 mt-6 border border-red-900/40 bg-red-950/20 rounded-xl px-5 py-4 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Results */}
        {results && results.length === 0 && !loading && (
          <div className="mt-8 text-muted text-sm text-center">
            no results found — try a different query
          </div>
        )}
        {results && results.length > 0 && filtered.length === 0 && (
          <div className="mt-2 text-muted text-sm text-center">
            nothing in that vibe — try a different one
          </div>
        )}
        {results && results.length > 0 && (
          <div className="animate-fade-in">
            <div className="mb-6 px-4">
              <SearchForm onSearch={handleSearch} loading={loading} compact />
            </div>

            {summary && (
              <p className="text-center text-xs text-white/35 italic tracking-wide mb-4 leading-relaxed px-4">
                {summary}
              </p>
            )}

            {/* Vibe filters + regenerate */}
            <div className="flex gap-2 mb-5 flex-wrap items-center px-4">
              {FILTERS.map(f => (
                <button
                  key={String(f.key)}
                  onClick={() => setFilter(f.key)}
                  className={`text-xs px-4 py-1.5 rounded-full border transition-all
                    ${filter === f.key
                      ? 'bg-accent text-bg border-accent font-semibold'
                      : 'border-subtle text-muted hover:text-ink hover:border-ink/20'
                    }`}
                >
                  {f.label}
                </button>
              ))}
              <button
                onClick={() => handleSearch(lastQuery)}
                disabled={loading}
                className="ml-auto text-xs text-muted hover:text-ink border border-subtle hover:border-ink/20
                           rounded-full px-4 py-1.5 transition-all disabled:opacity-30"
              >
                ↺ new batch
              </button>
            </div>

            {top && (
              <div className="mb-3">
                <RestaurantCard restaurant={top} featured date={meta.date} partySize={meta.party_size} city={meta.city} runId={runId} evalVerdict={evalVerdict} />
              </div>
            )}

            {others.length > 0 && (
              <>
                <p className="text-xs uppercase tracking-widest text-white/20 mb-2 px-4">other options</p>
                <div className="flex flex-col gap-1.5">
                  {others.map((r, i) => (
                    <RestaurantCard key={i} restaurant={r} date={meta.date} partySize={meta.party_size} city={meta.city} runId={runId} />
                  ))}
                </div>
              </>
            )}
          </div>
        )}
        </>)}
      </main>
    </div>
  )
}

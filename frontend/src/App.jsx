import { useState } from 'react'
import SearchForm from './components/SearchForm'
import AgentSteps from './components/AgentSteps'
import RestaurantCard from './components/RestaurantCard'

const API_URL = `http://localhost:${import.meta.env.VITE_API_PORT || '8003'}`

export default function App() {
  const [loading, setLoading]   = useState(false)
  const [results, setResults]   = useState(null)
  const [log, setLog]           = useState([])
  const [summary, setSummary]   = useState('')
  const [error, setError]       = useState('')
  const [query, setQuery]       = useState('')
  const [meta, setMeta]         = useState({})

  async function handleSearch(q) {
    setLoading(true)
    setError('')
    setResults(null)
    setLog([])
    setSummary('')
    setQuery(q)
    setMeta({})

    try {
      const res = await fetch(`${API_URL}/find-restaurant`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ query: q }),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Server error ${res.status}`)
      }

      const data = await res.json()
      setLog(data.log || [])
      setResults(data.recommendations || [])
      setSummary(data.final_answer || '')
      setMeta({ city: data.city, cuisine: data.cuisine, date: data.date, party_size: data.party_size })
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function handleReset() {
    setResults(null)
    setLog([])
    setSummary('')
    setError('')
    setQuery('')
    setMeta({})
  }

  const [top, ...others] = results || []

  return (
    <div className="min-h-screen bg-[#0F1117]">
      {/* Sidebar */}
      <aside className="fixed top-0 left-0 h-full w-72 bg-[#1A1D27] border-r border-white/08
                        flex flex-col p-6 z-10">
        <div className="mb-8">
          <h1 className="font-display text-xl font-bold text-white">🍽️ Restaurant Finder</h1>
          <p className="text-[#555E72] text-xs mt-1">LangGraph · Claude · ChromaDB</p>
        </div>

        <SearchForm onSearch={handleSearch} loading={loading} />

        {results && (
          <div className="mt-auto pt-6 border-t border-white/08">
            <p className="text-xs uppercase tracking-widest text-[#555E72] mb-3">Current search</p>
            {meta.city    && <p className="text-sm text-[#8A94A6] mb-1">📍 {meta.city}</p>}
            {meta.cuisine && <p className="text-sm text-[#8A94A6] mb-1">🍜 {meta.cuisine}</p>}
            {meta.date    && <p className="text-sm text-[#8A94A6] mb-3">📅 {meta.date}</p>}
            <button
              onClick={handleReset}
              className="w-full text-sm font-medium text-[#8A94A6] hover:text-white
                         border border-white/10 hover:border-white/20
                         rounded-lg py-2 transition-all duration-150"
            >
              🔄 New Search
            </button>
          </div>
        )}
      </aside>

      {/* Main */}
      <main className="ml-72 min-h-screen p-10">
        <div className="max-w-3xl mx-auto">

          {/* Error */}
          {error && (
            <div className="mb-6 bg-red-900/20 border border-red-500/30 rounded-xl px-5 py-4
                            text-red-400 text-sm animate-fade-in">
              ⚠️ {error}
              <p className="mt-1 text-red-500/70 text-xs">
                Make sure FastAPI is running: <code>./start.sh</code>
              </p>
            </div>
          )}

          {/* Agent steps */}
          {(log.length > 0 || loading) && (
            <AgentSteps log={log} loading={loading} />
          )}

          {/* Results */}
          {results && results.length > 0 ? (
            <div className="animate-fade-in">
              <h2 className="font-display text-3xl font-bold mb-2">Your recommendations</h2>
              {summary && (
                <p className="text-[#8A94A6] text-sm leading-relaxed mb-8">{summary}</p>
              )}

              {/* Top pick */}
              {top && (
                <div className="mb-6">
                  <RestaurantCard restaurant={top} featured date={meta.date} partySize={meta.party_size} city={meta.city} />
                </div>
              )}

              {/* Others */}
              {others.length > 0 && (
                <>
                  <div className="flex items-center gap-4 mb-5">
                    <div className="flex-1 h-px bg-white/08" />
                    <span className="text-xs uppercase tracking-widest text-[#555E72]">Other options</span>
                    <div className="flex-1 h-px bg-white/08" />
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {others.map((r, i) => (
                      <RestaurantCard key={i} restaurant={r} date={meta.date} partySize={meta.party_size} city={meta.city} />
                    ))}
                  </div>
                </>
              )}
            </div>
          ) : !loading && !error && (
            /* Landing */
            <div className="animate-fade-in">
              <h2 className="font-display text-3xl font-bold mb-2">Find your next table</h2>
              <p className="text-[#8A94A6] mb-8">
                Describe what you're looking for in plain English. The agent will research,
                enrich, and rank the best options for you.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { icon: '🔍', title: 'Research', desc: 'Searches OpenTable for matching restaurants' },
                  { icon: '📍', title: 'Enrich', desc: 'Pulls ratings, hours, and neighbourhood from Maps' },
                  { icon: '⭐', title: 'Recommend', desc: 'Ranks top 3 across price points with reasons' },
                ].map(({ icon, title, desc }) => (
                  <div key={title}
                       className="bg-[#1A1D27] border border-white/08 rounded-xl p-5">
                    <div className="text-2xl mb-3">{icon}</div>
                    <h3 className="font-semibold text-white mb-1">{title}</h3>
                    <p className="text-[#8A94A6] text-sm">{desc}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

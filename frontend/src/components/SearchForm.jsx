import { useState } from 'react'

const EXAMPLES = [
  'something cozy and Italian in NYC, Friday night for 2',
  'fancy anniversary dinner in Chicago, Saturday — impress me',
  'best ramen in London for 4, next weekend',
]

export default function SearchForm({ onSearch, loading, compact = false }) {
  const [query, setQuery] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (query.trim()) onSearch(query.trim())
  }

  if (compact) {
    return (
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="still hungry? search again…"
          disabled={loading}
          className="flex-1 bg-surface border border-subtle rounded-lg px-4 py-2.5
                     text-ink placeholder-muted text-sm
                     focus:outline-none focus:border-accent/50 transition-all disabled:opacity-40"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="bg-accent text-bg font-semibold text-sm px-5 py-2.5 rounded-lg
                     hover:bg-accent-light transition-all disabled:opacity-30"
        >
          {loading ? '…' : 'Go'}
        </button>
      </form>
    )
  }

  return (
    <div className="animate-fade-in">
      <h1 className="font-display text-5xl font-bold mb-3 leading-tight text-ink">
        what are you<br />craving?
      </h1>
      <p className="text-muted text-sm mb-10">
        describe the vibe, the city, the occasion. the agent handles the rest — research, rankings, and a table waiting for you.
      </p>

      <form onSubmit={handleSubmit} className="mb-10">
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="e.g. cozy Italian in NYC for 2, June 1st — nothing too loud"
          rows={3}
          disabled={loading}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e) }
          }}
          className="w-full bg-surface border border-subtle rounded-xl px-5 py-4
                     text-ink placeholder-muted text-sm resize-none
                     focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/20
                     transition-all disabled:opacity-40 mb-3"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="w-full bg-accent text-bg font-semibold text-sm py-3 rounded-xl
                     hover:bg-accent-light transition-all
                     disabled:opacity-30 disabled:cursor-not-allowed"
        >
          {loading ? 'sniffing out the best spots…' : "let's eat →"}
        </button>
      </form>

      <div className="space-y-2">
        <p className="text-xs text-muted uppercase tracking-widest mb-3">not sure? steal one of these</p>
        {EXAMPLES.map((ex, i) => (
          <button
            key={i}
            onClick={() => setQuery(ex)}
            disabled={loading}
            className="w-full text-left text-sm text-muted hover:text-ink
                       border border-subtle hover:border-ink/20 rounded-lg px-4 py-3
                       transition-all disabled:opacity-30"
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  )
}

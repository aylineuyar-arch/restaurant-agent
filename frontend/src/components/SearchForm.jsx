import { useState } from 'react'

const EXAMPLES = [
  'Vegan Japanese in NYC for 2, Friday at 7pm',
  'Fine dining Italian in Chicago for anniversary, Saturday night',
  'Best Thai in London for 4 people next weekend',
]

export default function SearchForm({ onSearch, loading }) {
  const [query, setQuery] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    if (query.trim()) onSearch(query.trim())
  }

  return (
    <div className="animate-fade-in">
      <h1 className="font-display text-4xl md:text-5xl font-bold mb-3 leading-tight">
        Find your next table
      </h1>
      <p className="text-[#8A94A6] text-base mb-8">
        Describe what you're looking for — city, cuisine, date, party size, dietary needs.
      </p>

      <form onSubmit={handleSubmit} className="mb-8">
        <div className="relative">
          <textarea
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="e.g. Vegan Japanese in NYC for 2, this Friday at 7pm"
            rows={3}
            disabled={loading}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e) }
            }}
            className="w-full bg-[#1A1D27] border border-white/10 rounded-xl px-5 py-4
                       text-[#E8ECF0] placeholder-[#555E72] text-base resize-none
                       focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20
                       transition-all duration-200 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="absolute bottom-3 right-3 bg-gradient-to-br from-primary to-primary-dark
                       text-white font-semibold text-sm px-5 py-2 rounded-lg
                       hover:from-primary-light hover:to-primary transition-all duration-200
                       shadow-[0_2px_8px_rgba(200,16,46,0.35)] hover:shadow-[0_4px_16px_rgba(200,16,46,0.45)]
                       hover:-translate-y-px disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none"
          >
            {loading ? 'Searching…' : 'Find →'}
          </button>
        </div>
      </form>

      {/* Example prompts */}
      <div>
        <p className="text-xs uppercase tracking-widest text-[#555E72] mb-3">Try an example</p>
        <div className="flex flex-col gap-2">
          {EXAMPLES.map((ex, i) => (
            <button
              key={i}
              onClick={() => setQuery(ex)}
              disabled={loading}
              className="text-left text-sm text-[#8A94A6] hover:text-[#E8ECF0]
                         bg-[#1A1D27] hover:bg-[#22263A] border border-white/08
                         rounded-lg px-4 py-3 transition-all duration-150
                         disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

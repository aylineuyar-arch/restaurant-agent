function Farfalle() {
  return (
    <svg width="80" height="56" viewBox="0 0 80 56" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Left wing */}
      <path
        d="M38 28 C30 18 12 10 4 16 C0 19 2 26 8 28 C2 30 0 37 4 40 C12 46 30 38 38 28Z"
        fill="#E8D5A3" stroke="#C9A84C" strokeWidth="1.2"
      />
      {/* Left wing ridges */}
      <path d="M20 16 C16 20 14 24 16 28" stroke="#C9A84C" strokeWidth="0.7" strokeLinecap="round" opacity="0.6"/>
      <path d="M12 20 C10 23 10 26 12 28" stroke="#C9A84C" strokeWidth="0.7" strokeLinecap="round" opacity="0.6"/>
      <path d="M20 40 C16 36 14 32 16 28" stroke="#C9A84C" strokeWidth="0.7" strokeLinecap="round" opacity="0.6"/>
      <path d="M12 36 C10 33 10 30 12 28" stroke="#C9A84C" strokeWidth="0.7" strokeLinecap="round" opacity="0.6"/>

      {/* Right wing */}
      <path
        d="M42 28 C50 18 68 10 76 16 C80 19 78 26 72 28 C78 30 80 37 76 40 C68 46 50 38 42 28Z"
        fill="#E8D5A3" stroke="#C9A84C" strokeWidth="1.2"
      />
      {/* Right wing ridges */}
      <path d="M60 16 C64 20 66 24 64 28" stroke="#C9A84C" strokeWidth="0.7" strokeLinecap="round" opacity="0.6"/>
      <path d="M68 20 C70 23 70 26 68 28" stroke="#C9A84C" strokeWidth="0.7" strokeLinecap="round" opacity="0.6"/>
      <path d="M60 40 C64 36 66 32 64 28" stroke="#C9A84C" strokeWidth="0.7" strokeLinecap="round" opacity="0.6"/>
      <path d="M68 36 C70 33 70 30 68 28" stroke="#C9A84C" strokeWidth="0.7" strokeLinecap="round" opacity="0.6"/>

      {/* Center pinch */}
      <ellipse cx="40" cy="28" rx="4" ry="7" fill="#D4A853" stroke="#C9A84C" strokeWidth="1.2"/>
      <ellipse cx="40" cy="28" rx="2" ry="4" fill="#E8C47A" opacity="0.6"/>
    </svg>
  )
}

const AGENTS = [
  { key: 'ParseNode',    label: 'Understanding your request',   model: 'Claude Haiku'  },
  { key: 'MemoryNode',   label: 'Checking past searches',       model: 'ChromaDB'      },
  { key: 'ResearchNode', label: 'Searching OpenTable',          model: 'Tavily'        },
  { key: 'MapsNode',     label: 'Enriching with Maps & reviews',model: 'Tavily'        },
  { key: 'RankNode',     label: 'Ranking your options',         model: 'Claude Sonnet' },
  { key: 'BookingNode',  label: 'Preparing reservation links',  model: 'LangGraph'     },
]

export default function AgentSteps({ log, loading }) {
  const doneNodes = new Set(
    (log || []).map(e => e.split(':')[0])
  )

  const activeIndex = AGENTS.findIndex(a => !doneNodes.has(a.key))
  const currentAgent = activeIndex >= 0 ? AGENTS[activeIndex] : null

  return (
    <div className="animate-fade-in py-12">
      {/* Spinning pasta while active */}
      {loading && (
        <div className="flex flex-col items-center gap-4 mb-12">
          <div
            className="animate-spin-pasta"
            style={{ display: 'inline-block', filter: 'drop-shadow(0 6px 16px rgba(201,168,76,0.35))' }}
          >
            <Farfalle />
          </div>
          {currentAgent && (
            <p className="text-muted text-sm tracking-wide">{currentAgent.label}…</p>
          )}
        </div>
      )}

      {/* Agent pipeline */}
      <div className="space-y-3">
        {AGENTS.map((agent, i) => {
          const done   = doneNodes.has(agent.key)
          const active = loading && i === activeIndex

          return (
            <div
              key={agent.key}
              className={`flex items-center gap-4 px-4 py-3 rounded-xl border transition-all duration-300
                ${done   ? 'border-accent/20 bg-accent/5'       : ''}
                ${active ? 'border-ink/15 bg-surface animate-pulse' : ''}
                ${!done && !active ? 'border-transparent opacity-30' : ''}
              `}
            >
              <span className={`text-lg w-6 text-center ${done ? '' : 'opacity-40'}`}>
                {done ? '✓' : active ? '◌' : '○'}
              </span>
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${done ? 'text-ink' : 'text-muted'}`}>
                  {agent.label}
                </p>
                <p className="text-xs text-muted mt-0.5">{agent.model}</p>
              </div>
              {done && (
                <span className="text-xs text-accent font-medium shrink-0">done</span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

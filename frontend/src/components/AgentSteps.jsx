const STEP_META = {
  ParseNode:    { label: 'Parsing your request',        icon: '🧠' },
  MemoryNode:   { label: 'Checking past searches',      icon: '🗄️' },
  ResearchNode: { label: 'Searching OpenTable',         icon: '🔍' },
  MapsNode:     { label: 'Enriching with Google Maps',  icon: '📍' },
  RankNode:     { label: 'Ranking recommendations',     icon: '⭐' },
  BookingNode:  { label: 'Reservation links ready',     icon: '✅' },
  EmailNode:    { label: 'Sending confirmation email',  icon: '📧' },
}

function Spinner() {
  return (
    <span className="flex gap-1 items-center">
      {[0, 1, 2].map(i => (
        <span
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse-dot"
          style={{ animationDelay: `${i * 0.16}s` }}
        />
      ))}
    </span>
  )
}

export default function AgentSteps({ log, loading }) {
  const steps = (log || []).map(entry => {
    const node = entry.split(':')[0]
    const meta = STEP_META[node] || { label: entry, icon: '•' }
    return { node, ...meta, raw: entry }
  })

  return (
    <div className="bg-[#1A1D27] border border-white/08 rounded-xl p-5 mb-8 animate-fade-in">
      <p className="text-xs uppercase tracking-widest text-[#555E72] mb-4">Agent progress</p>
      <div className="flex flex-col gap-3">
        {steps.map((s, i) => (
          <div key={i} className="flex items-center gap-3 text-sm animate-slide-up"
               style={{ animationDelay: `${i * 0.05}s` }}>
            <span className="text-base">{s.icon}</span>
            <span className="text-[#E8ECF0]">{s.label}</span>
            <span className="ml-auto text-[#2ECC71] text-xs font-medium">done</span>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-3 text-sm">
            <span className="text-base">⏳</span>
            <span className="text-[#8A94A6]">Working…</span>
            <span className="ml-auto"><Spinner /></span>
          </div>
        )}
      </div>
    </div>
  )
}

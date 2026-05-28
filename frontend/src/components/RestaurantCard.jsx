import { useState } from 'react'

const API_URL = `http://localhost:${import.meta.env.VITE_API_PORT || '8003'}`

export default function RestaurantCard({ restaurant, featured = false, date, partySize, city, runId, evalVerdict }) {
  const { name, neighborhood, price_range, reason, rating_info, rank } = restaurant
  const tags = Array.isArray(restaurant.tags) ? restaurant.tags : []
  const [status, setStatus]       = useState('idle')
  const [showModal, setShowModal] = useState(false)
  const [errorMsg, setErrorMsg]   = useState('')
  const [feedback, setFeedback]   = useState(null)  // null | 1 | -1

  async function submitFeedback(rating) {
    if (!runId || feedback !== null) return
    setFeedback(rating)
    try {
      await fetch(`${API_URL}/monitor/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: runId, restaurant: name, rating }),
      })
    } catch { /* silent */ }
  }

  async function confirmBooking() {
    setShowModal(false)
    setStatus('loading')
    try {
      const res = await fetch(`${API_URL}/book`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          restaurant_name: name,
          city:            city || '',
          date:            date || new Date().toISOString().split('T')[0],
          time_pref:       '7:00 PM',
          party_size:      partySize || 2,
          url:             restaurant.url || '',
        })
      })
      const data = await res.json()
      if (data.status === 'error') {
        setStatus('error')
        setErrorMsg(data.error)
      } else if (data.status === 'needs_selection') {
        setStatus('error')
        setErrorMsg('No slots found for that date. Try adjusting your search.')
      } else {
        setStatus('done')
      }
    } catch (e) {
      setStatus('error')
      setErrorMsg(e.message)
    }
  }

  return (
    <>
      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="bg-surface border border-subtle rounded-2xl p-8 max-w-sm w-full mx-4">
            <p className="text-muted text-xs uppercase tracking-widest mb-1">Confirm booking</p>
            <h3 className="font-display text-2xl font-bold text-ink mb-6">{name}</h3>
            <div className="space-y-1 mb-8 text-sm text-muted">
              {neighborhood && <p>{neighborhood}</p>}
              {date         && <p>{date} · 7:00 PM</p>}
              {partySize    && <p>{partySize} {partySize === 1 ? 'guest' : 'guests'}</p>}
            </div>
            <p className="text-xs text-muted mb-6 leading-relaxed">
              the agent will grab a time slot and shoot you an email. one click and your table's locked in.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 text-sm text-muted border border-subtle rounded-xl py-2.5
                           hover:text-ink hover:border-ink/20 transition-all"
              >
                Cancel
              </button>
              <button
                onClick={confirmBooking}
                className="flex-1 text-sm font-semibold bg-accent text-bg rounded-xl py-2.5
                           hover:bg-accent-light transition-all"
              >
                Book it →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Card */}
      <div className={`
        relative transition-all duration-200
        ${featured
          ? 'bg-gradient-to-br from-[#1C1A0F] to-[#0C0B08] border border-accent/50 rounded-2xl px-8 py-7 shadow-glow'
          : 'bg-[#111008] border border-white/5 hover:border-white/10 rounded-xl px-6 py-5'}
      `}>

        {featured && (
          <div className="flex items-center gap-2 mb-5">
            <span className="text-xs font-semibold tracking-widest uppercase text-accent">✦ top pick</span>
          </div>
        )}

        <div className="flex items-start gap-4">
          {!featured && (
            <span className="font-display text-xl font-bold mt-0.5 w-6 shrink-0 text-white/20">{rank}</span>
          )}
          <div className="flex-1 min-w-0">
            <h2 className={`font-display font-bold text-ink leading-tight mb-1 ${featured ? 'text-3xl' : 'text-lg'}`}>
              {name}
            </h2>
            <div className="flex items-center gap-3 text-xs text-muted mb-3">
              {neighborhood && <span>{neighborhood}</span>}
              {neighborhood && price_range && <span>·</span>}
              {price_range && (
                <span className={featured ? 'text-accent font-medium' : 'text-white/40'}>{price_range}</span>
              )}
            </div>

            {/* Tags */}
            {tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mb-4">
                {tags.slice(0, 3).map((tag, i) => (
                  <span key={i} className={`text-xs px-2.5 py-0.5 rounded-full border
                    ${featured
                      ? 'border-accent/30 text-accent/80 bg-accent/5'
                      : 'border-white/10 text-white/40 bg-white/3'}`}>
                    {tag}
                  </span>
                ))}
              </div>
            )}

            {reason && (
              <p className={`leading-relaxed mb-3 ${featured ? 'text-sm text-ink/80' : 'text-xs text-white/40 line-clamp-2'}`}>
                {reason}
              </p>
            )}

            {/* AI eval verdict — featured card only */}
            {featured && evalVerdict && (
              <p className="text-xs text-accent/60 italic mb-4">
                ✦ AI eval: {evalVerdict}
              </p>
            )}

            {/* Feedback thumbs */}
            {runId && (
              <div className="flex items-center gap-2 mb-4">
                <span className="text-xs text-muted">was this a good pick?</span>
                <button
                  onClick={() => submitFeedback(1)}
                  disabled={feedback !== null}
                  className={`text-sm px-2 py-0.5 rounded transition-all ${feedback === 1 ? 'text-emerald-400' : 'text-muted hover:text-emerald-400 disabled:opacity-40'}`}
                >
                  👍
                </button>
                <button
                  onClick={() => submitFeedback(-1)}
                  disabled={feedback !== null}
                  className={`text-sm px-2 py-0.5 rounded transition-all ${feedback === -1 ? 'text-red-400' : 'text-muted hover:text-red-400 disabled:opacity-40'}`}
                >
                  👎
                </button>
                {feedback !== null && (
                  <span className="text-xs text-muted">got it, thanks</span>
                )}
              </div>
            )}

            {/* Status */}
            {status === 'done' && (
              <p className="text-sm text-accent font-medium">your table's basically set. check your inbox.</p>
            )}
            {status === 'error' && (
              <p className="text-sm text-red-400">something went sideways — {errorMsg}</p>
            )}
            {status === 'loading' && (
              <p className="text-sm text-muted animate-pulse">pulling strings in the kitchen…</p>
            )}

            {/* Button */}
            {status === 'idle' && (
              <button
                onClick={() => setShowModal(true)}
                className={`text-sm font-semibold transition-all
                  ${featured
                    ? 'bg-accent text-bg px-6 py-2.5 rounded-xl hover:bg-accent-light'
                    : 'text-accent hover:text-accent-light border border-accent/30 hover:border-accent/60 rounded-lg px-4 py-2'
                  }`}
              >
                Book on OpenTable →
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

import { useState } from 'react'

const API_URL = `http://localhost:${import.meta.env.VITE_API_PORT || '8003'}`

export default function RestaurantCard({ restaurant, featured = false, date, partySize, city }) {
  const { name, neighborhood, price_range, reason, rating_info, url, rank } = restaurant
  const [status, setStatus]         = useState('idle')
  const [confirmation, setConfirmation] = useState(null)
  const [errorMsg, setErrorMsg]     = useState('')

  async function handleBook() {
    setStatus('loading')
    setErrorMsg('')
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
        })
      })
      const data = await res.json()
      if (data.status === 'error') {
        setStatus('error')
        setErrorMsg(data.error)
      } else if (data.status === 'needs_selection') {
        setStatus('needs_selection')
        setErrorMsg(data.message)
      } else if (data.status === 'pending_confirmation') {
        setStatus('pending_confirmation')
      } else {
        setStatus('booked')
        setConfirmation(data.confirmation)
      }
    } catch (e) {
      setStatus('error')
      setErrorMsg(e.message)
    }
  }

  return (
    <div className={`
      group relative bg-[#1A1D27] border rounded-2xl p-6
      transition-all duration-200 hover:-translate-y-1 hover:shadow-hover animate-slide-up
      ${featured ? 'border-primary/40 shadow-glow shadow-card' : 'border-white/08 shadow-card hover:bg-[#22263A]'}
    `}>
      {featured && (
        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-primary to-primary-dark rounded-l-2xl" />
      )}

      <div className="flex items-start justify-between gap-4 mb-3">
        <div>
          {featured && (
            <span className="inline-flex items-center gap-1 text-xs font-semibold bg-primary/15 text-primary rounded-full px-2.5 py-0.5 mb-2">
              ⭐ Top Pick
            </span>
          )}
          <h2 className={`font-display font-bold leading-tight ${featured ? 'text-2xl' : 'text-xl'}`}>
            {featured ? name : `${rank}. ${name}`}
          </h2>
          {neighborhood && <p className="text-[#8A94A6] text-sm mt-1">📍 {neighborhood}</p>}
        </div>
        {price_range && (
          <span className="shrink-0 text-secondary text-sm font-semibold bg-secondary/10 rounded-lg px-3 py-1 whitespace-nowrap">
            {price_range}
          </span>
        )}
      </div>

      {reason     && <p className="text-[#E8ECF0] text-sm leading-relaxed mb-3">{reason}</p>}
      {rating_info && <p className="text-[#8A94A6] text-xs mb-4">{rating_info}</p>}

      {/* Status banners */}
      {status === 'booked' && (
        <div className="mb-4 bg-green-900/20 border border-green-500/30 rounded-xl px-4 py-3">
          <p className="text-green-400 text-sm font-semibold">✓ Reservation completed</p>
          {confirmation && <p className="text-green-400/70 text-xs mt-1">Confirmation: #{confirmation}</p>}
        </div>
      )}
      {status === 'pending_confirmation' && (
        <div className="mb-4 bg-blue-900/20 border border-blue-500/30 rounded-xl px-4 py-3">
          <p className="text-blue-400 text-sm font-semibold">📧 Check your email</p>
          <p className="text-blue-400/70 text-xs mt-1">Agent selected a time slot — click the link in your email to confirm.</p>
        </div>
      )}
      {(status === 'error' || status === 'needs_selection') && (
        <div className="mb-4 bg-yellow-900/20 border border-yellow-500/30 rounded-xl px-4 py-3">
          <p className="text-yellow-400 text-xs">⚠️ {errorMsg}</p>
        </div>
      )}

      {/* Book button */}
      {status === 'loading' ? (
        <div className="w-full text-center text-sm text-white/60 bg-[#22263A] border border-white/08 rounded-xl py-3 animate-pulse">
          Agent booking in Chrome…
        </div>
      ) : status === 'booked' ? (
        <div className="w-full text-center text-sm font-medium text-green-400 border border-green-500/30 rounded-xl py-3">
          ✓ Booked
        </div>
      ) : status === 'pending_confirmation' ? (
        <div className="w-full text-center text-sm font-medium text-blue-400 border border-blue-500/30 rounded-xl py-3">
          📧 Email sent — confirm to lock it in
        </div>
      ) : (
        <button
          onClick={handleBook}
          className="block w-full text-center text-sm font-semibold text-white
                     bg-gradient-to-br from-primary to-primary-dark rounded-xl py-3
                     hover:from-primary-light hover:to-primary
                     shadow-[0_2px_8px_rgba(200,16,46,0.3)]
                     hover:shadow-[0_4px_16px_rgba(200,16,46,0.45)]
                     hover:-translate-y-px transition-all duration-200"
        >
          {status === 'needs_selection' ? 'Retry Booking →' : 'Book on OpenTable →'}
        </button>
      )}
    </div>
  )
}

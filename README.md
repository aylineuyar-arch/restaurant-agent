# Fork Yea! — AI Restaurant Reservation Agent

**Part of [AylinOS](https://github.com/aylineuyar-arch/aylinos)** — six live agents, one router.
**Live demos & case studies:** [aylin-uyar-portfolio.lovable.app](https://aylin-uyar-portfolio.lovable.app)

A portfolio-quality multi-agent AI app that goes from a natural-language request to a restaurant recommendation and booking confirmation — with live workflow observability built in.

## What it does

Type something like *"great date night spot in NYC on Friday, two people, something a bit fancy"* and the agent pipeline kicks off:

1. **Parse** — Claude Haiku extracts city, cuisine, date, party size, and vibe from plain English
2. **Memory** — ChromaDB checks past searches to skip redundant lookups
3. **Research** — Tavily searches OpenTable and surfaces real, bookable restaurants
4. **Retry** — if fewer than 3 results come back, automatically broadens the query
5. **Enrich** — pulls neighborhood, price range, ratings, and tags for each candidate
6. **Rank** — Claude Sonnet selects 6 recommendations across 3 price tiers (casual / mid-range / high-end) with written reasoning
7. **Evaluate** — Claude Haiku acts as an LLM judge: independently scores and writes a one-sentence verdict on the top pick
8. **Book** — Playwright connects to Chrome via CDP and attempts the OpenTable reservation; falls back to a direct search URL if bot detection blocks it
9. **Notify** — Resend fires a transactional email with the checkout link

Every step streams live to the UI as it completes.

## Stack

| Layer | Tech |
|---|---|
| Agent graph | LangGraph (StateGraph with conditional edges) |
| LLMs | Claude Haiku (parse, evaluate) + Claude Sonnet (rank) |
| Search | Tavily API |
| Vector memory | ChromaDB |
| Browser automation | Playwright over Chrome CDP |
| Transactional email | Resend |
| API | FastAPI with Server-Sent Events |
| Observability | SQLite (WAL mode) + custom monitor dashboard |
| Frontend | React + Vite + Tailwind CSS |

## Features

### Live agent pipeline
Every node in the LangGraph workflow streams a status update to the UI via Server-Sent Events. Users see checkmarks appear in real time as Parse → Memory → Research → Enrich → Rank → Evaluate → Book completes.

### Vibe filters + regeneration
Results are tagged by tier. Filter pills — "no dress code", "treat yourself", "full send" — narrow results client-side without re-running the agent. A "↺ new batch" button re-runs the same query for a fresh set of recommendations.

### LLM-as-judge evaluation
After Sonnet ranks the results, Haiku independently evaluates the top pick and returns a score (0–1) and a one-sentence verdict. The verdict appears on the featured card; the score is logged to Monitor.

### User feedback loop
Every restaurant card has 👍/👎 buttons. Ratings are persisted to SQLite and surface in the Monitor run detail panel alongside the node trace.

### Monitor Mode
A built-in observability dashboard (toggle "⬡ monitor" in the header) shows:
- **Stats row**: total runs, success rate, avg latency, escalation count
- **Runs table**: query, status, latency, recommendation count, confidence score, AI eval score, timestamp
- **Escalation queue**: runs flagged for review when confidence < 0.5 or no recs returned
- **Run detail modal**: node pipeline timeline (proportional latency bars per node), metadata grid, user feedback
- Auto-refreshes every 30 seconds

### Confidence scoring and escalation
Each run gets an algorithmic confidence score (starts at 1.0, penalized for errors, retries, zero results). Low-confidence runs are flagged and surfaced in the review queue.

## Architecture

```
User query
    │
    ▼
parse_input (Haiku) ──────────────────── extracts city, cuisine, date, party size
    │
    ▼
check_memory (ChromaDB) ──────────────── skip re-research if seen before
    │
    ▼
research (Tavily → OpenTable)
    │
    ├─ < 3 results → retry_research (broader query)
    │
    ▼
enrich (Tavily → Google Maps) ────────── neighborhood, ratings, price, tags
    │
    ▼
rank (Sonnet) ────────────────────────── 6 recs, 2 per tier, with reasoning
    │
    ▼
evaluate (Haiku, LLM-as-judge) ──────── score + verdict on top pick
    │
    ▼
book (Playwright → Chrome CDP) ──────── OpenTable slot selection; falls back to search URL
    │
    ▼
send_email (Resend) ─────────────────── checkout link or direct booking confirmation
    │
    ▼
Monitor DB (SQLite) ─────────────────── run trace, confidence, eval score, user feedback
```

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/aylineuyar-arch/restaurant-agent.git
cd restaurant-agent
cp .env.example .env
```

Edit `.env`:
- `ANTHROPIC_API_KEY` — from [console.anthropic.com](https://console.anthropic.com)
- `TAVILY_API_KEY` — from [tavily.com](https://tavily.com)
- `RESEND_API_KEY` — from [resend.com](https://resend.com)
- `NOTIFICATION_EMAIL` — where to send reservation links

### 2. Install dependencies

Python 3.10+, Node 18+ required.

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

cd frontend && npm install && cd ..
```

### 3. Run

```bash
./start.sh
```

Opens on `http://localhost:5173`. The FastAPI backend runs on port 8003.

## Notes

- Booking connects to an isolated Chrome profile — your personal Chrome data is never touched
- OpenTable bot detection occasionally blocks headless browsers; the agent emails a direct search URL as fallback so you always get a response
- Monitor Mode data persists in `monitor.db` (SQLite, WAL mode) between server restarts

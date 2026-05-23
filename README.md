# Restaurant Reservation Agent

An agentic AI workflow that researches, ranks, and initiates OpenTable reservations from a single natural-language request.

## What it does

1. **Parse** — extracts city, cuisine, date, party size from plain English using Claude Haiku
2. **Memory** — checks ChromaDB for past searches to personalize recommendations
3. **Research** — searches OpenTable via Tavily for matching restaurants
4. **Enrich** — pulls ratings, neighborhood, and price info for each candidate
5. **Rank** — Claude Sonnet picks the top 3 across different price points with reasoning
6. **Book** — Playwright connects to an isolated Chrome instance, navigates to OpenTable, and selects a time slot
7. **Notify** — sends you an email with the pre-filled checkout link to confirm with one click

## Stack

| Layer | Tech |
|---|---|
| Agent graph | LangGraph |
| LLM | Claude Haiku (parse) + Claude Sonnet (rank) |
| Search | Tavily API |
| Vector memory | ChromaDB |
| Browser automation | Playwright over Chrome CDP |
| API | FastAPI |
| Frontend | React + Vite + Tailwind CSS |

## Setup

### 1. Clone and configure

```bash
git clone https://github.com/aylineuyar-arch/restaurant-agent.git
cd restaurant-agent
cp .env.example .env
```

Edit `.env` and add:
- `ANTHROPIC_API_KEY` — from [console.anthropic.com](https://console.anthropic.com)
- `TAVILY_API_KEY` — from [tavily.com](https://tavily.com)
- `EMAIL_SENDER` + `EMAIL_PASSWORD` — Gmail + [App Password](https://myaccount.google.com/apppasswords)
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

This starts FastAPI, React, and an isolated Chrome instance (separate from your personal Chrome profile). Open the URL printed in the terminal.

## Usage

Type a request in plain English:

> *Italian restaurant in NYC for 2 on June 1*

The agent researches, enriches, and ranks options. Click **Book on OpenTable →** on any result — the agent selects a time slot and emails you a direct checkout link.

## Architecture

```
User query
    │
    ▼
parse_input (Haiku)
    │
    ▼
check_memory (ChromaDB)
    │
    ▼
research (Tavily → OpenTable)
    │
    ├─ < 3 results → retry_research (broader query)
    │
    ▼
enrich (Tavily → Google Maps)
    │
    ▼
rank (Sonnet) → recommendations
    │
    ▼
/book endpoint
    │
    ▼
Playwright CDP → isolated Chrome → OpenTable time slot
    │
    ▼
Email: "Complete your reservation →"
```

## Notes

- Booking automation connects to an isolated Chrome profile at `.chrome-dev-profile/` — your personal Chrome data is never touched
- Email is sent via Gmail SMTP; requires an App Password (not your account password)
- OpenTable requires sign-in to complete a reservation — the agent handles everything up to checkout and emails you the link

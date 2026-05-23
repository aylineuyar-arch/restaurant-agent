import json
import os
import re
import httpx
import anthropic
from datetime import datetime
from dotenv import load_dotenv

from state import AgentState
from memory_store import search_memory, save_to_memory
from tools import (
    search_opentable,
    search_google_maps,
    open_booking_page,
    send_confirmation_email,
)

load_dotenv()

_trust_env = os.getenv("ANTHROPIC_HTTP_TRUST_ENV", "0").lower() in ("1", "true", "yes")
_http_client = httpx.Client(trust_env=_trust_env, timeout=60.0)
claude = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    http_client=_http_client,
)


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError("No JSON found in response")


# ── Node 1: Parse natural language input ──────────────────────────────────────

def parse_input(state: AgentState) -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        # Use Haiku — cheap model, simple extraction task
        response = claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{
                "role": "user",
                "content": f'Today:{today}. Extract JSON from: "{state["query"]}"\n{{"city":"","cuisine":"","date":"YYYY-MM-DD","party_size":2,"vegan":false,"user_email":null}}'
            }]
        )
        parsed = _extract_json(response.content[0].text)
        return {
            "city":       parsed.get("city", ""),
            "cuisine":    parsed.get("cuisine", ""),
            "date":       parsed.get("date", today),
            "party_size": int(parsed.get("party_size", 2)),
            "vegan":      bool(parsed.get("vegan", False)),
            "user_email": parsed.get("user_email"),
            "log": [f"ParseNode: {parsed.get('cuisine')} in {parsed.get('city')} "
                    f"for {parsed.get('party_size')} on {parsed.get('date')}"]
        }
    except Exception as e:
        return {
            "city": "",
            "cuisine": "",
            "date": today,
            "party_size": 2,
            "vegan": False,
            "user_email": None,
            "log": [f"ParseNode error: {type(e).__name__}: {e}"],
        }


# ── Node 2: Check ChromaDB memory ────────────────────────────────────────────

def check_memory(state: AgentState) -> dict:
    past = search_memory(state["city"], state["cuisine"])
    return {
        "past_searches": past,
        "log": [f"MemoryNode: {len(past)} past search(es) found"]
    }


# ── Node 3: Search OpenTable ─────────────────────────────────────────────────

def research(state: AgentState) -> dict:
    try:
        results = search_opentable(
            city=state["city"],
            cuisine=state["cuisine"],
            date=state["date"],
            party_size=state["party_size"],
            vegan=state.get("vegan", False),
        )
        return {
            "raw_results": results,
            "log": [f"ResearchNode: {len(results)} OpenTable result(s)"]
        }
    except Exception as e:
        return {
            "raw_results": [],
            "log": [f"ResearchNode error: {type(e).__name__}: {e}"],
        }


# ── Node 3b: Retry with broader query ───────────────────────────────────────

def retry_research(state: AgentState) -> dict:
    try:
        results = search_opentable(
            city=state["city"],
            cuisine=state["cuisine"],
            date=state["date"],
            party_size=state["party_size"],
            vegan=False,  # drop vegan filter to broaden
        )
        return {
            "raw_results": results,
            "retry_count": state.get("retry_count", 0) + 1,
            "log": [f"ResearchNode retry (vegan filter removed): {len(results)} result(s)"]
        }
    except Exception as e:
        return {
            "raw_results": [],
            "retry_count": state.get("retry_count", 0) + 1,
            "log": [f"ResearchNode retry error: {type(e).__name__}: {e}"],
        }


# ── Node 4: Enrich with Google Maps ─────────────────────────────────────────

def enrich(state: AgentState) -> dict:
    enriched = []
    for r in state["raw_results"][:3]:
        try:
            maps = search_google_maps(r["name"], state["city"])
            enriched.append({**r, "maps_info": maps.get("info", "")})
        except Exception as e:
            enriched.append({**r, "maps_info": "", "maps_error": str(e)})
    return {
        "enriched_results": enriched,
        "log": [f"MapsNode: enriched {len(enriched)} result(s) with Google Maps"]
    }


# ── Node 5: Claude ranks and recommends ─────────────────────────────────────

def _trim_candidates(enriched: list) -> list:
    """Strip heavy fields before sending to Claude — keep only what ranking needs."""
    return [{
        "name":        r.get("name", ""),
        "url":         r.get("url", ""),
        "info":        ((r.get("maps_info") or "") + " " + (r.get("description") or ""))[:350].strip(),
    } for r in enriched]


def rank(state: AgentState) -> dict:
    candidates = json.dumps(_trim_candidates(state["enriched_results"]))
    past = state.get("past_searches") or []
    past_line = ""
    if past:
        cities_cuisines = [{"city": p.get("meta", {}).get("city"), "cuisine": p.get("meta", {}).get("cuisine")} for p in past[:2]]
        past_line = f"Past: {json.dumps(cities_cuisines)}\n"

    try:
        response = claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": f"""Rank for: "{state['query']}"
{past_line}Candidates: {candidates}
Return exactly 6 restaurants: 2 casual, 2 mid-range, 2 high-end. JSON:
{{"recommendations":[{{"rank":1,"name":"","url":"","reason":"1-2 sentences","rating_info":"","price_range":"$X-$Y/person","neighborhood":"","tags":["casual","cuisine type","occasion"]}}],"summary":"one punchy vibe line, max 12 words, no restaurant names"}}
CRITICAL: First tag of each item MUST be exactly one of: "casual", "mid-range", "high-end". Return all 6."""
            }]
        )
        parsed = _extract_json(response.content[0].text)
        recs   = parsed.get("recommendations", [])
        top    = recs[0] if recs else {}
        return {
            "recommendations": recs,
            "top_url":         top.get("url", ""),
            "final_answer":    parsed.get("summary", ""),
            "log": [f"RankNode: top pick is {top.get('name', 'unknown')}"]
        }
    except Exception as e:
        return {
            "recommendations": [],
            "final_answer": "",
            "log": [f"RankNode error: {type(e).__name__}: {e}"],
        }


# ── Node 6: Booking page ready (user clicks in UI) ───────────────────────────

def book(state: AgentState) -> dict:
    url = state.get("top_url", "")
    return {
        "booking_status": "ready" if url else "no_url",
        "log": [f"BookingNode: reservation links ready"]
    }


# ── Node 7: Save to ChromaDB ─────────────────────────────────────────────────

def save(state: AgentState) -> dict:
    try:
        save_to_memory(
            city=state["city"],
            cuisine=state["cuisine"],
            date=state["date"],
            recommendations=state.get("recommendations", [])
        )
        return {"log": ["MemoryNode: saved to ChromaDB"]}
    except Exception as e:
        return {"log": [f"MemoryNode save error: {type(e).__name__}: {e}"]}


# ── Node 8: Send confirmation email (conditional) ────────────────────────────

def send_email(state: AgentState) -> dict:
    recs = state.get("recommendations", [])
    if not recs:
        return {"email_status": "skipped_no_recs", "log": ["EmailNode: skipped"]}

    result = send_confirmation_email(
        to_email=state["user_email"],
        restaurant_name=recs[0]["name"],
        date=state["date"],
        party_size=state["party_size"],
        booking_url=state["top_url"],
    )
    return {
        "email_status": result.get("status", "unknown"),
        "log": [f"EmailNode: {result.get('status')}"]
    }


# ── Conditional edge functions ───────────────────────────────────────────────

def should_retry(state: AgentState) -> str:
    too_few = len(state.get("raw_results", [])) < 3
    under_limit = state.get("retry_count", 0) < 1
    return "retry" if (too_few and under_limit) else "enrich"


def should_email(state: AgentState) -> str:
    return "send_email" if state.get("user_email") else "__end__"

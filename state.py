from typing import TypedDict, Annotated, Optional
import operator


class AgentState(TypedDict):
    # ── Input ──────────────────────────────────────────────
    query:      str
    city:       str
    cuisine:    str
    date:       str
    party_size: int
    vegan:      bool
    user_email: Optional[str]

    # ── Research ───────────────────────────────────────────
    past_searches:    list
    raw_results:      list
    enriched_results: list
    retry_count:      int

    # ── Output ─────────────────────────────────────────────
    recommendations: list
    top_url:         str
    booking_status:  str
    email_status:    str
    final_answer:    str

    # Accumulates across all nodes (reducer)
    log: Annotated[list[str], operator.add]

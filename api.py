import os
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from graph import run_graph, stream_graph
from booking import book_restaurant

load_dotenv()

for _proxy_var in (
    "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
    "ALL_PROXY", "all_proxy", "SOCKS_PROXY", "SOCKS5_PROXY",
):
    os.environ.pop(_proxy_var, None)

app = FastAPI(title="Restaurant Agent API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class BookRequest(BaseModel):
    restaurant_name: str
    city:            str
    date:            str
    time_pref:       str
    party_size:      int
    url:             str = ""


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/find-restaurant")
def find_restaurant(request: QueryRequest):
    """Standard JSON endpoint — runs full graph, returns when done."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        result = run_graph(request.query)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Agent failed: {type(e).__name__}: {e}")
    return _build_result(result)


@app.get("/find-restaurant-stream")
def find_restaurant_stream(q: str):
    """SSE streaming endpoint (GET) — compatible with EventSource API in all browsers."""
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    def generate():
        final_state = {}
        try:
            for node_name, output in stream_graph(q):
                final_state.update(output)
                event = {"node": node_name, "log": output.get("log", [])}
                yield f"data: {json.dumps(event)}\n\n"
            yield f"data: {json.dumps({'done': True, **_build_result(final_state)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _build_result(state: dict) -> dict:
    return {
        "recommendations": state.get("recommendations", []),
        "final_answer":    state.get("final_answer", ""),
        "booking_status":  state.get("booking_status", ""),
        "city":            state.get("city", ""),
        "cuisine":         state.get("cuisine", ""),
        "date":            state.get("date", ""),
        "party_size":      state.get("party_size", 2),
        "log":             state.get("log", []),
    }


@app.post("/book")
def book(request: BookRequest):
    if not request.restaurant_name.strip():
        raise HTTPException(status_code=400, detail="Restaurant name required")
    try:
        result = book_restaurant(
            restaurant_name=request.restaurant_name,
            city=request.city,
            date=request.date,
            time_pref=request.time_pref,
            party_size=request.party_size,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Booking failed: {e}")

    # Agent reached the pre-filled checkout page — email the link
    checkout_url = result.get("final_url") or request.url
    if result.get("status") in ("pending_confirmation", "completed") and checkout_url:
        _send_reservation_email(
            restaurant_name=request.restaurant_name,
            date=request.date,
            party_size=request.party_size,
            checkout_url=checkout_url,
        )
        result["email_sent"] = True

    return result


def _send_reservation_email(restaurant_name: str, date: str, party_size: int, checkout_url: str):
    api_key  = os.getenv("RESEND_API_KEY")
    to_email = os.getenv("NOTIFICATION_EMAIL", "aylin.e.uyar@gmail.com")

    if not api_key:
        return  # Email not configured — silently skip

    try:
        import resend
        resend.api_key = api_key
        resend.Emails.send({
            "from":    "Restaurant Agent <onboarding@resend.dev>",
            "to":      [to_email],
            "subject": f"your AI got you a table. don't blow it. ({restaurant_name})",
            "text":    f"""Your agent has selected a table for you.

Restaurant:  {restaurant_name}
Date:        {date}
Party size:  {party_size}

Click below to confirm your reservation:

{checkout_url}

This takes you directly to the OpenTable checkout — sign in and hit Confirm.
""",
        })
    except Exception:
        pass  # Don't fail the booking response if email errors

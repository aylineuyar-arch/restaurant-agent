import os
import json
import time
import uuid
import threading
import queue as _queue
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from graph import run_graph, stream_graph
from booking import book_restaurant
import monitor_db
from monitor_routes import router as monitor_router

load_dotenv()

for _proxy_var in (
    "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
    "ALL_PROXY", "all_proxy", "SOCKS_PROXY", "SOCKS5_PROXY",
):
    os.environ.pop(_proxy_var, None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    monitor_db.init_db()
    yield


app = FastAPI(title="Restaurant Agent API", version="2.0", lifespan=lifespan)

app.include_router(monitor_router)

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
        run_id     = str(uuid.uuid4())
        wall_start = time.monotonic()
        monitor_db.create_run(run_id, q)

        final_state  = {}
        node_traces  = []
        seq          = 0
        prev_ts      = wall_start
        result_q     = _queue.Queue()

        def _run_agent():
            try:
                for node_name, output in stream_graph(q):
                    result_q.put(("node", node_name, output))
                result_q.put(("done", None, None))
            except Exception as e:
                result_q.put(("error", str(e), None))

        threading.Thread(target=_run_agent, daemon=True).start()

        try:
            while True:
                try:
                    msg_type, node_name, output = result_q.get(timeout=15)
                except _queue.Empty:
                    # Send SSE comment to keep Railway/proxy from timing out
                    yield ": keepalive\n\n"
                    continue

                if msg_type == "error":
                    total_ms = int((time.monotonic() - wall_start) * 1000)
                    monitor_db.finalize_run(run_id, total_ms, 0, node_traces, False, 0, status="error")
                    yield f"data: {json.dumps({'error': node_name})}\n\n"
                    break

                if msg_type == "done":
                    result     = _build_result(final_state)
                    total_ms   = int((time.monotonic() - wall_start) * 1000)
                    ran_retry  = any("retry" in l.lower() for l in final_state.get("log", []))
                    raw_count  = len(final_state.get("raw_results", []))
                    recs_count = len(result.get("recommendations", []))
                    eval_score = final_state.get("eval_score", 0.0)
                    monitor_db.finalize_run(run_id, total_ms, recs_count, node_traces, ran_retry,
                                            raw_count, eval_score=eval_score)
                    yield f"data: {json.dumps({'done': True, 'run_id': run_id, **result})}\n\n"
                    break

                now        = time.monotonic()
                latency_ms = int((now - prev_ts) * 1000)
                prev_ts    = now

                log_entry   = (output.get("log") or [""])[0]
                node_status = "error" if "error" in log_entry.lower() else "ok"

                monitor_db.upsert_node_trace(run_id, seq, node_name, latency_ms, node_status, log_entry)
                node_traces.append({"status": node_status})
                seq += 1

                final_state.update(output)
                yield f"data: {json.dumps({'node': node_name, 'log': output.get('log', [])})}\n\n"

        except GeneratorExit:
            total_ms = int((time.monotonic() - wall_start) * 1000)
            monitor_db.finalize_run(run_id, total_ms, 0, node_traces, False, 0, status="error")

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
        "eval_score":      state.get("eval_score", 0.0),
        "eval_verdict":    state.get("eval_verdict", ""),
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

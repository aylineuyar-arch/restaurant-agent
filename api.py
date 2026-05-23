import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from graph import run_graph
from booking import book_restaurant

load_dotenv()

for _proxy_var in (
    "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
    "ALL_PROXY", "all_proxy", "SOCKS_PROXY", "SOCKS5_PROXY",
):
    os.environ.pop(_proxy_var, None)

app = FastAPI(title="Restaurant Agent API", version="2.0")

_ui_port = os.getenv("UI_PORT", "5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"http://localhost:{_ui_port}",
        f"http://127.0.0.1:{_ui_port}",
    ],
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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/find-restaurant")
def find_restaurant(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    try:
        result = run_graph(request.query)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Agent failed: {type(e).__name__}: {e}",
        ) from e

    log = result.get("log", [])
    final_answer = result.get("final_answer", "")
    if not final_answer and any("error" in entry.lower() for entry in log):
        final_answer = (
            "Could not complete the full search (see log). "
            "Check ANTHROPIC_API_KEY, TAVILY_API_KEY, and network/proxy settings."
        )

    return {
        "recommendations": result.get("recommendations", []),
        "final_answer":    final_answer,
        "booking_status":  result.get("booking_status", ""),
        "email_status":    result.get("email_status", ""),
        "log":             log,
        "city":            result.get("city", ""),
        "cuisine":         result.get("cuisine", ""),
        "date":            result.get("date", ""),
        "party_size":      result.get("party_size", 2),
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

    # Send "complete your reservation" email when agent reaches checkout page
    if result.get("status") == "pending_confirmation" and result.get("final_url"):
        _send_reservation_email(
            restaurant_name=request.restaurant_name,
            date=request.date,
            party_size=request.party_size,
            checkout_url=result["final_url"],
        )
        result["email_sent"] = True

    return result


def _send_reservation_email(restaurant_name: str, date: str, party_size: int, checkout_url: str):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    sender   = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    to_email = os.getenv("NOTIFICATION_EMAIL") or sender

    if not sender or not password:
        return  # Email not configured — silently skip

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Complete your reservation — {restaurant_name}"
    msg["From"]    = sender
    msg["To"]      = to_email

    body = f"""\
Your agent has selected a table for you.

  Restaurant:  {restaurant_name}
  Date:        {date}
  Party size:  {party_size}

The time slot is reserved and waiting. Click below to confirm:

  {checkout_url}

This link takes you directly to the OpenTable checkout page.
Sign in and hit Confirm to lock in your reservation.
"""
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
    except Exception:
        pass  # Don't fail the booking response if email errors

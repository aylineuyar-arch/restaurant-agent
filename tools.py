import os
import json
import webbrowser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from tavily import TavilyClient
from dotenv import load_dotenv

# Clear proxy vars injected by Cursor/IDE that block external API calls
for _v in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy",
           "ALL_PROXY", "all_proxy", "SOCKS_PROXY", "SOCKS5_PROXY"):
    os.environ.pop(_v, None)

load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")


# ── ResearchAgent ──────────────────────────────────────────────────────────────

import re as _re

# Only accept direct restaurant pages — not list/feature/blog pages
_BLOCKED_PATTERNS = _re.compile(
    r'opentable\.com/(features|blog|list|best|s\?|m\?|collections)',
    _re.IGNORECASE
)
_RESTAURANT_PATTERN = _re.compile(
    r'opentable\.com/(r/|restaurant/|\w+-\w+)',
    _re.IGNORECASE
)

def search_opentable(city: str, cuisine: str, date: str, party_size: int, vegan: bool = False) -> list[dict]:
    dietary = "vegan " if vegan else ""
    query = f'site:opentable.com/r/ {dietary}{cuisine} restaurant {city}'
    results = tavily.search(
        query=query,
        search_depth="basic",
        max_results=5,
        include_domains=["opentable.com"]
    )
    restaurants = []
    for r in results.get("results", []):
        url = r.get("url", "")
        # Skip list/feature pages, only keep direct restaurant pages
        if _BLOCKED_PATTERNS.search(url):
            continue
        if "opentable.com" not in url:
            continue
        restaurants.append({
            "name":        r.get("title", "").replace(" - OpenTable", "").replace(" | OpenTable", "").strip(),
            "url":         url,
            "description": r.get("content", "")[:200],
        })
    return restaurants[:3]


def search_multiple_cities(cities: list[str], cuisine: str, date: str, party_size: int, vegan: bool = False) -> dict:
    all_results = {}
    for city in cities:
        all_results[city] = search_opentable(city, cuisine, date, party_size, vegan)
    return all_results


# ── MapsAgent ─────────────────────────────────────────────────────────────────

def search_google_maps(restaurant_name: str, city: str) -> dict:
    query = f"{restaurant_name} {city} restaurant rating price neighborhood"
    results = tavily.search(query=query, search_depth="basic", max_results=1)
    if results.get("results"):
        r = results["results"][0]
        return {
            "name": restaurant_name,
            "info": r.get("content", "")[:300],
        }
    return {"name": restaurant_name, "info": ""}


# ── MemoryAgent ───────────────────────────────────────────────────────────────

def get_memory() -> list[dict]:
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save_memory(city: str, cuisine: str, date: str, recommendations: list[dict]) -> dict:
    memory = get_memory()
    memory.append({
        "timestamp": datetime.now().isoformat(),
        "city": city,
        "cuisine": cuisine,
        "date": date,
        "recommendations": recommendations
    })
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)
    return {"status": "saved", "total_searches": len(memory)}


# ── BookingAgent ──────────────────────────────────────────────────────────────

def open_booking_page(url: str) -> dict:
    webbrowser.open(url)
    return {"status": "opened", "url": url}


# ── EmailAgent ────────────────────────────────────────────────────────────────

def send_confirmation_email(to_email: str, restaurant_name: str, date: str, party_size: int, booking_url: str) -> dict:
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")

    if not sender or not password:
        return {"status": "skipped", "reason": "EMAIL_SENDER or EMAIL_PASSWORD not set in .env"}

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Reservation reminder — {restaurant_name}"
    msg["From"] = sender
    msg["To"] = to_email

    body = f"""Hi,

Here are your reservation details:

  Restaurant:  {restaurant_name}
  Date:        {date}
  Party size:  {party_size}
  Book here:   {booking_url}

Enjoy your meal!
"""
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, to_email, msg.as_string())
        return {"status": "sent", "to": to_email}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

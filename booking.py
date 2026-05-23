import asyncio
import re
from urllib.parse import quote_plus
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# Isolated Chrome from ./start.sh: CDP on 127.0.0.1:9222, user-data-dir .chrome-dev-profile.
# Does not use personal Chrome under ~/Library/Application Support/Google/Chrome/.
CHROME_CDP_URL = "http://127.0.0.1:9222"


def _to_24h(time_str: str) -> str:
    try:
        import datetime
        t = datetime.datetime.strptime(time_str.strip(), "%I:%M %p")
        return t.strftime("%H:%M")
    except Exception:
        return "19:00"


def build_search_url(restaurant_name: str, city: str, date: str, time_pref: str, party_size: int) -> str:
    time_24 = _to_24h(time_pref)
    aliases = {'NYC': 'New York', 'LA': 'Los Angeles', 'SF': 'San Francisco', 'DC': 'Washington'}
    city_full = aliases.get((city or '').upper(), city or '')
    term = quote_plus(restaurant_name.strip())
    loc  = f"&location={quote_plus(city_full)}" if city_full else ""
    return (
        f"https://www.opentable.com/s?"
        f"covers={party_size}&datetime={date}+{time_24}"
        f"&term={term}{loc}&lang=en-US"
    )


async def book_opentable(restaurant_name: str, city: str, date: str, time_pref: str, party_size: int) -> dict:
    search_url = build_search_url(restaurant_name, city, date, time_pref, party_size)

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(CHROME_CDP_URL)
            print("✅ Connected to isolated Chrome")
        except Exception as e:
            return {
                "status": "error",
                "error":  "Could not connect to isolated Chrome on port 9222. Run ./start.sh first.",
                "search_url": search_url
            }

        # Get or create a context, always open a fresh page
        try:
            context = browser.contexts[0]
        except Exception:
            context = await browser.new_context()
        page = await context.new_page()

        try:
            print(f"🔍 Navigating to OpenTable search for {restaurant_name}...")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(4000)

            # ── Click the first available time slot ───────────────────────────
            # Selectors from OpenTable's live HTML (verified 2026-05)
            slot_selectors = [
                'a[role="button"][aria-label*="Reserve table"]',
                '[data-testid^="time-slot-"] a',
                '[data-test^="time-slot-"] a',
                '[data-test="time-slots"] a',
            ]
            clicked_slot = False
            for sel in slot_selectors:
                try:
                    await page.wait_for_selector(sel, timeout=6000)
                    slots = await page.query_selector_all(sel)
                    if slots:
                        slot_label = await slots[0].get_attribute("aria-label") or ""
                        await slots[0].click()
                        await page.wait_for_load_state("domcontentloaded")
                        await page.wait_for_timeout(2000)
                        clicked_slot = True
                        print(f"✅ Clicked slot: {slot_label}")
                        break
                except PWTimeout:
                    continue

            if not clicked_slot:
                return {
                    "status":     "needs_selection",
                    "message":    "OpenTable loaded but no available time slots were found for that date/time. Try a different date or restaurant.",
                    "search_url": search_url,
                }

            # ── Stop here — return the pre-filled checkout URL ────────────────
            # The caller (api.py /book) sends an email with this link so the
            # user can complete the reservation with one click.
            print(f"✅ Reached checkout: {page.url}")
            return {
                "status":    "pending_confirmation",
                "final_url": page.url,
                "search_url": search_url,
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "search_url": search_url}


def book_restaurant(restaurant_name: str, city: str, date: str, time_pref: str, party_size: int) -> dict:
    return asyncio.run(book_opentable(restaurant_name, city, date, time_pref, party_size))

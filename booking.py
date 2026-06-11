import asyncio
from typing import Optional
from urllib.parse import quote_plus

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


async def _try_cdp_booking(search_url: str, restaurant_name: str) -> Optional[dict]:
    """Attempt slot-click via pre-launched CDP Chrome. Returns None if CDP unavailable."""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return None  # Playwright not installed (e.g. on Railway) — fall back to URL email

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(CHROME_CDP_URL)
        except Exception:
            return None  # CDP not available — caller will fall back to URL email

        print("✅ Connected to isolated Chrome via CDP")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        page    = await context.new_page()

        try:
            print(f"🔍 Navigating to OpenTable for: {restaurant_name}")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(4000)

            slot_selectors = [
                'a[role="button"][aria-label*="Reserve table"]',
                '[data-testid^="time-slot-"] a',
                '[data-test^="time-slot-"] a',
                '[data-test="time-slots"] a',
            ]
            for sel in slot_selectors:
                try:
                    await page.wait_for_selector(sel, timeout=6000)
                    slots = await page.query_selector_all(sel)
                    if not slots:
                        continue
                    slot_label = await slots[0].get_attribute("aria-label") or sel
                    await slots[0].click()
                    await page.wait_for_timeout(3000)
                    try:
                        await page.wait_for_load_state("domcontentloaded", timeout=5000)
                    except Exception:
                        pass
                    final_url = page.url
                    print(f"✅ Clicked slot: {slot_label} → {final_url}")
                    return {"status": "pending_confirmation", "final_url": final_url,
                            "search_url": search_url, "slot_found": True}
                except Exception:
                    continue

            print("⚠️  No time slots found via CDP")
            return {"status": "pending_confirmation", "final_url": search_url,
                    "search_url": search_url, "slot_found": False}

        except Exception as e:
            print(f"❌ CDP booking error: {e}")
            return {"status": "pending_confirmation", "final_url": search_url,
                    "search_url": search_url, "slot_found": False}
        finally:
            try:
                await page.close()
            except Exception:
                pass


def book_restaurant(restaurant_name: str, city: str, date: str, time_pref: str, party_size: int) -> dict:
    search_url = build_search_url(restaurant_name, city, date, time_pref, party_size)

    # Try CDP Chrome first (requires start.sh to have launched it)
    result = asyncio.run(_try_cdp_booking(search_url, restaurant_name))

    if result is None:
        # CDP unavailable — skip browser entirely, email the search URL directly
        print("⚙️  CDP unavailable — skipping browser, emailing search URL")
        result = {
            "status":     "pending_confirmation",
            "final_url":  search_url,
            "search_url": search_url,
            "slot_found": False,
        }

    return result

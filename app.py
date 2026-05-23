import streamlit as st
import httpx

import os
_port_file = os.path.join(os.path.dirname(__file__), ".api_port")
_port = open(_port_file).read().strip() if os.path.exists(_port_file) else "8003"
API_URL = f"http://localhost:{_port}"

st.set_page_config(page_title="Restaurant Finder", layout="wide")

# ── Professional UI/UX CSS injection ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

/* ── Color system ── */
:root {
    --color-primary:    #C8102E;
    --color-primary-lt: #E8344A;
    --color-primary-dk: #9B0D22;
    --color-secondary:  #F5A623;
    --color-accent:     #2C7BE5;
    --color-bg:         #0F1117;
    --color-surface:    #1A1D27;
    --color-surface-2:  #22263A;
    --color-border:     rgba(255,255,255,0.08);
    --color-text:       #E8ECF0;
    --color-text-muted: #8A94A6;
    --color-text-faint: #555E72;
    --color-success:    #2ECC71;
    --color-warning:    #F39C12;
    --color-error:      #E74C3C;
    --space-xs:  4px;
    --space-sm:  8px;
    --space-md:  16px;
    --space-lg:  24px;
    --space-xl:  40px;
    --radius-sm: 6px;
    --radius-md: 12px;
    --radius-lg: 20px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.3);
    --shadow-md: 0 4px 16px rgba(0,0,0,0.4);
    --shadow-lg: 0 8px 32px rgba(0,0,0,0.5);
    --shadow-glow: 0 0 24px rgba(200,16,46,0.18);
    --transition: 0.2s ease;
}

/* ── Typography ── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--color-text) !important;
    -webkit-font-smoothing: antialiased;
}
h1 {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 2.6rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px !important;
    line-height: 1.15 !important;
    color: var(--color-text) !important;
}
h2 {
    font-size: 1.75rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.3px !important;
    color: var(--color-text) !important;
}
h3 {
    font-size: 1.3rem !important;
    font-weight: 600 !important;
    color: var(--color-text) !important;
}
p, li, .stMarkdown p {
    font-size: 0.95rem !important;
    line-height: 1.65 !important;
    color: var(--color-text) !important;
}
small, .stCaption, [data-testid="stCaptionContainer"] p {
    font-size: 0.8rem !important;
    color: var(--color-text-muted) !important;
    letter-spacing: 0.01em !important;
}

/* ── Page chrome ── */
.main .block-container {
    padding-top: var(--space-xl) !important;
    padding-bottom: var(--space-xl) !important;
    max-width: 1100px !important;
}
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
html { scroll-behavior: smooth; }

/* ── Dividers ── */
hr, [data-testid="stDivider"] {
    border: none !important;
    border-top: 1px solid var(--color-border) !important;
    margin: var(--space-lg) 0 !important;
}

/* ── Cards (bordered containers) ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: var(--color-surface) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: var(--radius-md) !important;
    padding: var(--space-lg) !important;
    box-shadow: var(--shadow-md) !important;
    transition: transform var(--transition), box-shadow var(--transition),
                background var(--transition) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] > div:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-lg) !important;
    background: var(--color-surface-2) !important;
}

/* ── Featured card accent bar ── */
.card-featured [data-testid="stVerticalBlockBorderWrapper"] > div {
    border-left: 4px solid var(--color-primary) !important;
    box-shadow: var(--shadow-md), var(--shadow-glow) !important;
}

/* ── Buttons ── */
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dk)) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.02em !important;
    padding: 0.6rem 1.4rem !important;
    transition: all var(--transition) !important;
    box-shadow: 0 2px 8px rgba(200,16,46,0.3) !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="baseButton-primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(200,16,46,0.45) !important;
    background: linear-gradient(135deg, var(--color-primary-lt), var(--color-primary)) !important;
}
.stButton > button:not([kind="primary"]) {
    background: transparent !important;
    border: 1px solid var(--color-border) !important;
    color: var(--color-text) !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 500 !important;
    transition: all var(--transition) !important;
}
.stButton > button:not([kind="primary"]):hover {
    border-color: var(--color-primary) !important;
    color: var(--color-primary) !important;
}

/* ── Link buttons (st.link_button / Book on OpenTable) ── */
.stLinkButton > a {
    background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dk)) !important;
    color: #fff !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    letter-spacing: 0.02em !important;
    text-decoration: none !important;
    padding: 0.55rem 1.2rem !important;
    display: block !important;
    text-align: center !important;
    transition: all var(--transition) !important;
    box-shadow: 0 2px 8px rgba(200,16,46,0.25) !important;
}
.stLinkButton > a:hover {
    background: linear-gradient(135deg, var(--color-primary-lt), var(--color-primary)) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(200,16,46,0.4) !important;
}

/* ── Form inputs ── */
.stTextArea textarea,
.stTextInput input {
    background: var(--color-surface-2) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--color-text) !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.92rem !important;
    transition: border-color var(--transition), box-shadow var(--transition) !important;
}
.stTextArea textarea:focus,
.stTextInput input:focus {
    border-color: var(--color-primary) !important;
    box-shadow: 0 0 0 3px rgba(200,16,46,0.15) !important;
    outline: none !important;
}
.stTextArea label, .stTextInput label {
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.02em !important;
    color: var(--color-text-muted) !important;
    text-transform: uppercase !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--color-surface) !important;
    border-right: 1px solid var(--color-border) !important;
}
[data-testid="stSidebar"] h1 {
    font-size: 1.35rem !important;
}
[data-testid="stSidebar"] [data-testid="stDivider"] {
    border-color: var(--color-border) !important;
}

/* ── Info blocks (st.info) ── */
div[data-testid="stNotification"] {
    background: var(--color-surface-2) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: var(--radius-md) !important;
    border-left: 4px solid var(--color-accent) !important;
    transition: transform var(--transition), box-shadow var(--transition) !important;
}
div[data-testid="stNotification"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-md) !important;
}

/* ── Status widget ── */
[data-testid="stStatusWidget"] {
    background: var(--color-surface) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: var(--radius-md) !important;
}

/* ── Loading pulse animation ── */
@keyframes pulse-border {
    0%   { box-shadow: 0 0 0 0   rgba(200,16,46,0.4); }
    70%  { box-shadow: 0 0 0 10px rgba(200,16,46,0); }
    100% { box-shadow: 0 0 0 0   rgba(200,16,46,0); }
}

/* ── Mobile responsiveness ── */
@media (max-width: 768px) {
    h1 { font-size: 1.9rem !important; }
    h2 { font-size: 1.35rem !important; }
    .main .block-container {
        padding-left: var(--space-md) !important;
        padding-right: var(--space-md) !important;
    }
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        padding: var(--space-md) !important;
    }
    [data-testid="stSidebarCollapsedControl"] button {
        background: var(--color-primary) !important;
        color: #fff !important;
        border-radius: 50% !important;
    }
}
@media (max-width: 480px) {
    h1 { font-size: 1.5rem !important; }
    .stButton > button { font-size: 0.85rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "results"  not in st.session_state: st.session_state.results  = None
if "summary"  not in st.session_state: st.session_state.summary  = ""
if "query"    not in st.session_state: st.session_state.query    = ""
if "city"     not in st.session_state: st.session_state.city     = ""
if "cuisine"  not in st.session_state: st.session_state.cuisine  = ""
if "date"     not in st.session_state: st.session_state.date     = ""

NODE_LABELS = {
    "ParseNode":    "Parsing your request",
    "MemoryNode":   "Checking past searches",
    "ResearchNode": "Searching OpenTable",
    "MapsNode":     "Enriching with Google Maps",
    "RankNode":     "Ranking recommendations",
    "BookingNode":  "Reservation links ready",
    "EmailNode":    "Sending confirmation email",
}

# ── Helper ────────────────────────────────────────────────────────────────────
def render_card(r, is_top=False):
    if is_top:
        # Featured card: accent bar on the left via wrapper div
        st.markdown('<div class="card-featured">', unsafe_allow_html=True)

    with st.container(border=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            if is_top:
                # Badge + name on the same line
                st.markdown(
                    f'<span style="background:var(--color-primary);color:#fff;border-radius:20px;'
                    f'padding:3px 12px;font-size:0.72rem;font-weight:700;letter-spacing:0.08em;'
                    f'text-transform:uppercase;">Top Pick</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(f"## ⭐ {r['name']}")
            else:
                st.markdown(f"### {r['rank']}. {r['name']}")
            if r.get("neighborhood"):
                st.caption(f"📍 {r['neighborhood']}")
        with col2:
            if r.get("price_range"):
                st.markdown(
                    f'<div style="font-weight:700;font-size:1.05rem;color:var(--color-secondary);'
                    f'text-align:right;padding-top:4px;">{r["price_range"]}</div>',
                    unsafe_allow_html=True,
                )

        if r.get("reason"):
            st.markdown(r["reason"])
        if r.get("rating_info"):
            st.caption(r["rating_info"])

        if r.get("url"):
            st.link_button("Book on OpenTable →", r["url"], use_container_width=True)

    if is_top:
        st.markdown('</div>', unsafe_allow_html=True)


def call_api(query: str) -> dict:
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(f"{API_URL}/find-restaurant", json={"query": query})
        resp.raise_for_status()
        return resp.json()


# ── Search panel (sidebar) ────────────────────────────────────────────────────
with st.sidebar:
    st.title("🍽️ Restaurant Finder")
    st.caption("LangGraph · Claude · ChromaDB")
    st.divider()

    with st.form("search_form"):
        query = st.text_area(
            "What are you looking for?",
            value=st.session_state.query,
            placeholder="e.g. Vegan Japanese in NYC for 2, Friday 7pm",
            height=100
        )
        submitted = st.form_submit_button("Find Restaurants", type="primary", use_container_width=True)

    if st.session_state.results:
        st.divider()
        st.markdown("**Current search**")
        if st.session_state.city:
            st.caption(f"📍 {st.session_state.city}")
        if st.session_state.cuisine:
            st.caption(f"🍜 {st.session_state.cuisine}")
        if st.session_state.date:
            st.caption(f"📅 {st.session_state.date}")
        st.divider()
        if st.button("🔄 New Search", use_container_width=True):
            st.session_state.results = None
            st.session_state.summary = ""
            st.session_state.query   = ""
            st.rerun()


# ── Main content ──────────────────────────────────────────────────────────────
if not st.session_state.results:
    # Landing state
    st.title("Find your next table")
    st.markdown(
        "Describe what you're looking for in plain English — city, cuisine, date, party size, dietary needs.",
        unsafe_allow_html=False,
    )
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**Quick dinner**\n\nVegan Japanese in NYC for 2, this Friday at 7pm")
    with col2:
        st.info("**Special occasion**\n\nFine dining Italian in Chicago for anniversary, Saturday")
    with col3:
        st.info("**Travel planning**\n\nBest Thai in London or Paris for 4 people next weekend")

if submitted and query.strip():
    st.session_state.query = query

    with st.status("Agent searching...", expanded=True) as status:
        for label in NODE_LABELS.values():
            pass  # placeholder — log entries drive this below

        try:
            data = call_api(query)

            for entry in data.get("log", []):
                node = entry.split(":")[0]
                label = NODE_LABELS.get(node, entry)
                st.write(f"✓ {label}")

            status.update(label="Search complete", state="complete")
            st.session_state.results  = data.get("recommendations", [])
            st.session_state.summary  = data.get("final_answer", "")
            st.session_state.city     = data.get("city", "")
            st.session_state.cuisine  = data.get("cuisine", "")
            st.session_state.date     = data.get("date", "")

        except Exception as e:
            status.update(label="Error", state="error")
            st.error(f"Could not reach API: {e}\n\nMake sure the server is running on port 8003.")
            st.stop()

    st.rerun()

# ── Results view ──────────────────────────────────────────────────────────────
if st.session_state.results:
    recs = st.session_state.results

    st.title("Your recommendations")
    if st.session_state.summary:
        st.markdown(st.session_state.summary)

    # Section divider with label
    st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin:24px 0 20px;">
  <div style="flex:1;height:1px;background:var(--color-border);"></div>
  <span style="font-size:0.72rem;font-weight:700;letter-spacing:0.12em;
               text-transform:uppercase;color:var(--color-text-muted);">Top Pick</span>
  <div style="flex:1;height:1px;background:var(--color-border);"></div>
</div>
""", unsafe_allow_html=True)

    # Top pick — full width, starred, featured card
    if recs:
        render_card(recs[0], is_top=True)

    # Remaining options side by side
    others = recs[1:]
    if others:
        st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin:32px 0 16px;">
  <div style="flex:1;height:1px;background:var(--color-border);"></div>
  <span style="font-size:0.72rem;font-weight:700;letter-spacing:0.12em;
               text-transform:uppercase;color:var(--color-text-muted);">Other options</span>
  <div style="flex:1;height:1px;background:var(--color-border);"></div>
</div>
""", unsafe_allow_html=True)
        cols = st.columns(len(others))
        for col, r in zip(cols, others):
            with col:
                render_card(r, is_top=False)

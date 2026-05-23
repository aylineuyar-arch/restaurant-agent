#!/bin/bash
# ── Restaurant Agent — one-command startup ────────────────────────────────────
# Dev booking uses an isolated Chrome profile (.chrome-dev-profile), not your
# personal Chrome data under ~/Library/Application Support/Google/Chrome/.

cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy SOCKS_PROXY SOCKS5_PROXY

# ── Check .env ────────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  echo "⚠️  No .env found — created from template."
  echo "👉 Open .env, add your keys, then run ./start.sh again."
  exit 1
fi

source .env

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_anthropic_key_here" ]; then
  echo "❌ ANTHROPIC_API_KEY not set in .env"; exit 1
fi
if [ -z "$TAVILY_API_KEY" ] || [ "$TAVILY_API_KEY" = "your_tavily_key_here" ]; then
  echo "❌ TAVILY_API_KEY not set in .env"; exit 1
fi

# ── Find python + pip ─────────────────────────────────────────────────────────
PYTHON=$(which python3 || which python)
PIP="$PYTHON -m pip"

# Prefer venv if it exists
if [ -f venv/bin/python ]; then
  PYTHON="$(pwd)/venv/bin/python"
  PIP="$PYTHON -m pip"
  STREAMLIT="$(pwd)/venv/bin/streamlit"
else
  STREAMLIT=$(which streamlit 2>/dev/null || echo "$PYTHON -m streamlit")
fi

# ── Python deps ───────────────────────────────────────────────────────────────
if ! $PYTHON -c "import langgraph" 2>/dev/null; then
  echo "📦 Installing Python dependencies..."
  $PIP install -q -r requirements.txt
fi

# ── Node deps ─────────────────────────────────────────────────────────────────
if [ ! -d frontend/node_modules ]; then
  echo "📦 Installing Node dependencies..."
  cd frontend && npm install && cd ..
fi

# ── Stop stale processes from a previous run ──────────────────────────────────
for pidfile in .api_pid .react_pid; do
  if [ -f "$pidfile" ]; then
    old_pid=$(cat "$pidfile")
    if kill -0 "$old_pid" 2>/dev/null; then
      kill "$old_pid" 2>/dev/null || true
      sleep 0.5
    fi
    rm -f "$pidfile"
  fi
done

# Also kill anything still listening on our usual ports (orphaned dev servers)
kill_listeners_on_ports() {
  for port in "$@"; do
    pids=$(lsof -ti :"$port" -sTCP:LISTEN 2>/dev/null || true)
    if [ -n "$pids" ]; then
      echo "🛑 Stopping stale listener on port $port (PID $pids)..."
      kill $pids 2>/dev/null || true
    fi
  done
  sleep 0.5
}
kill_listeners_on_ports 8003 8004 8005 8006 8007 8008
kill_listeners_on_ports 5173 5174 5175 5176 5177 5178

# ── Find free ports ───────────────────────────────────────────────────────────
find_free_port() {
  for port in "$@"; do
    if ! lsof -i :$port -sTCP:LISTEN &>/dev/null; then echo $port; return; fi
  done
  echo "${@: -1}"
}

API_PORT=$(find_free_port 8003 8004 8005 8006 8007 8008)
UI_PORT=$(find_free_port 5173 5174 5175 5176 5177 5178)
export UI_PORT

echo $API_PORT > .api_port
echo $UI_PORT > .ui_port
echo "✅ API port: $API_PORT"
echo "✅ UI port:  $UI_PORT"

# ── Start FastAPI ─────────────────────────────────────────────────────────────
$PYTHON -m uvicorn api:app --host 0.0.0.0 --port $API_PORT > uvicorn.log 2>&1 &
API_PID=$!
echo $API_PID > .api_pid

for i in {1..10}; do
  if curl -s http://127.0.0.1:$API_PORT/health > /dev/null 2>&1; then
    echo "✅ FastAPI is up (PID $API_PID)"; break
  fi
  sleep 1
done

# ── Write port for React to pick up ──────────────────────────────────────────
echo "VITE_API_PORT=$API_PORT" > frontend/.env.local

# ── Start React dev server ────────────────────────────────────────────────────
echo "⚛️  Starting React on port $UI_PORT..."
cd frontend && npm run dev -- --port "$UI_PORT" &
REACT_PID=$!
cd ..
echo $REACT_PID > .react_pid

for i in {1..10}; do
  if curl -s "http://localhost:$UI_PORT" > /dev/null 2>&1; then
    echo "✅ Vite is up (PID $REACT_PID)"; break
  fi
  sleep 1
done

UI_URL="http://localhost:${UI_PORT}/"

# ── Isolated Chrome for Playwright (CDP port 9222) ────────────────────────────
# Never touches ~/Library/Application Support/Google/Chrome/ (personal profile).
CHROME_USER_DATA_DIR="$PROJECT_DIR/.chrome-dev-profile"
CHROME_DEVTOOLS_PORT=9222
CHROME_BIN="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
mkdir -p "$CHROME_USER_DATA_DIR"

chrome_isolated_running() {
  pgrep -f "user-data-dir=${CHROME_USER_DATA_DIR}" >/dev/null 2>&1
}

# ── Start isolated Chrome in background (for Playwright CDP only) ─────────────
if ! chrome_isolated_running; then
  if [ -x "$CHROME_BIN" ]; then
    echo "🤖 Starting booking Chrome (background, port $CHROME_DEVTOOLS_PORT)..."
    "$CHROME_BIN" \
      --remote-debugging-port="$CHROME_DEVTOOLS_PORT" \
      --remote-allow-origins="*" \
      --user-data-dir="$CHROME_USER_DATA_DIR" \
      --profile-directory=Default \
      --no-first-run \
      --no-default-browser-check \
      --window-position=10000,10000 \
      --window-size=1280,800 \
      "about:blank" >/dev/null 2>&1 &
    sleep 2
    echo "✅ Booking Chrome ready on CDP port $CHROME_DEVTOOLS_PORT"
  else
    echo "⚠️  Google Chrome not found — booking automation unavailable"
  fi
else
  echo "✅ Booking Chrome already running"
fi

# ── Open UI in Safari ─────────────────────────────────────────────────────────
echo "🌐 Opening UI in Safari..."
open -a Safari "$UI_URL"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  👉 OPEN THIS URL:  $UI_URL"
echo "  ⚛️  UI  →  http://localhost:$UI_PORT"
echo "  🔌 API →  http://localhost:$API_PORT/health"
echo "  Press Ctrl+C to stop everything"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

trap "kill $API_PID $REACT_PID 2>/dev/null; rm -f .api_pid .api_port .react_pid .ui_port; echo 'Stopped.'" EXIT

wait $REACT_PID

"""
SQLite persistence layer for Monitor Mode.
Thread-safe via a module-level Lock — FastAPI runs SSE generators in thread pool threads.
"""
import sqlite3
import threading
from typing import Optional
from datetime import datetime, timezone

DB_PATH = "monitor.db"

_lock = threading.Lock()
_conn: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA foreign_keys=ON")
    return _conn


def init_db():
    with _lock:
        conn = _get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS monitor_runs (
                run_id                TEXT PRIMARY KEY,
                query                 TEXT NOT NULL,
                started_at            TEXT NOT NULL,
                finished_at           TEXT,
                total_latency_ms      INTEGER,
                recommendations_count INTEGER DEFAULT 0,
                confidence_score      REAL    DEFAULT 1.0,
                eval_score            REAL    DEFAULT 0.0,
                escalated             INTEGER DEFAULT 0,
                estimated_cost_usd    REAL    DEFAULT 0.0,
                status                TEXT    DEFAULT 'running'
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id       TEXT NOT NULL,
                restaurant   TEXT NOT NULL,
                rating       INTEGER NOT NULL,
                created_at   TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_feedback_run_id ON feedback(run_id);

            CREATE TABLE IF NOT EXISTS monitor_node_traces (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id      TEXT    NOT NULL REFERENCES monitor_runs(run_id) ON DELETE CASCADE,
                seq         INTEGER NOT NULL,
                node_name   TEXT    NOT NULL,
                latency_ms  INTEGER NOT NULL,
                status      TEXT    NOT NULL DEFAULT 'ok',
                log         TEXT    NOT NULL DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_traces_run_id ON monitor_node_traces(run_id);
        """)
        conn.commit()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_run(run_id: str, query: str):
    with _lock:
        _get_conn().execute(
            "INSERT INTO monitor_runs (run_id, query, started_at, status) VALUES (?,?,?,'running')",
            (run_id, query, now_iso())
        )
        _get_conn().commit()


def upsert_node_trace(run_id: str, seq: int, node_name: str, latency_ms: int, status: str, log: str):
    with _lock:
        _get_conn().execute(
            "INSERT INTO monitor_node_traces (run_id, seq, node_name, latency_ms, status, log) VALUES (?,?,?,?,?,?)",
            (run_id, seq, node_name, latency_ms, status, log)
        )
        _get_conn().commit()


def _compute_confidence(node_traces: list, recs_count: int, ran_retry: bool, raw_results_count: int) -> float:
    score = 1.0
    error_nodes = sum(1 for t in node_traces if t["status"] == "error")
    score -= min(error_nodes * 0.2, 0.4)
    if recs_count == 0:
        score -= 0.5
    elif recs_count < 3:
        score -= 0.2
    if ran_retry:
        score -= 0.15
    if raw_results_count == 0:
        score -= 0.2
    return round(max(0.0, min(1.0, score)), 2)


def finalize_run(run_id: str, total_latency_ms: int, recs_count: int,
                 node_traces: list, ran_retry: bool, raw_results_count: int,
                 status: str = "done", eval_score: float = 0.0):
    confidence = _compute_confidence(node_traces, recs_count, ran_retry, raw_results_count)
    escalated  = 1 if (confidence < 0.5 or recs_count == 0) else 0
    cost       = round(0.004 + (0.001 if ran_retry else 0), 4)

    with _lock:
        _get_conn().execute("""
            UPDATE monitor_runs SET
                finished_at           = ?,
                total_latency_ms      = ?,
                recommendations_count = ?,
                confidence_score      = ?,
                eval_score            = ?,
                escalated             = ?,
                estimated_cost_usd    = ?,
                status                = ?
            WHERE run_id = ?
        """, (now_iso(), total_latency_ms, recs_count, confidence, eval_score, escalated, cost, status, run_id))
        _get_conn().commit()

    return confidence, bool(escalated)


def save_feedback(run_id: str, restaurant: str, rating: int):
    with _lock:
        _get_conn().execute(
            "INSERT INTO feedback (run_id, restaurant, rating, created_at) VALUES (?,?,?,?)",
            (run_id, restaurant, rating, now_iso())
        )
        _get_conn().commit()


def get_feedback(run_id: str) -> list:
    with _lock:
        rows = _get_conn().execute(
            "SELECT restaurant, rating, created_at FROM feedback WHERE run_id=? ORDER BY created_at",
            (run_id,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Read helpers ──────────────────────────────────────────────────────────────

def get_stats() -> dict:
    with _lock:
        conn = _get_conn()
        row = conn.execute("""
            SELECT
                COUNT(*)                                       AS total_runs,
                AVG(total_latency_ms)                          AS avg_latency_ms,
                SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) AS success_count,
                SUM(escalated)                                 AS escalated_count,
                AVG(confidence_score)                          AS avg_confidence,
                AVG(estimated_cost_usd)                        AS avg_cost_usd,
                SUM(CASE WHEN date(started_at)=date('now') THEN 1 ELSE 0 END) AS runs_today
            FROM monitor_runs WHERE status != 'running'
        """).fetchone()

        total = row["total_runs"] or 0
        success = row["success_count"] or 0
        return {
            "total_runs":     total,
            "avg_latency_ms": round(row["avg_latency_ms"] or 0),
            "success_rate":   round((success / total * 100) if total else 0, 1),
            "escalated_count":row["escalated_count"] or 0,
            "avg_confidence": round(row["avg_confidence"] or 0, 2),
            "avg_cost_usd":   round(row["avg_cost_usd"] or 0, 4),
            "runs_today":     row["runs_today"] or 0,
        }


def get_runs(limit: int = 50, offset: int = 0, escalated_only: bool = False) -> list:
    with _lock:
        where = "WHERE escalated=1" if escalated_only else ""
        rows = _get_conn().execute(f"""
            SELECT run_id, query, started_at, finished_at, total_latency_ms,
                   recommendations_count, confidence_score, escalated,
                   estimated_cost_usd, status
            FROM monitor_runs {where}
            ORDER BY started_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()
    return [dict(r) for r in rows]


def get_run(run_id: str) -> Optional[dict]:
    with _lock:
        run = _get_conn().execute(
            "SELECT * FROM monitor_runs WHERE run_id=?", (run_id,)
        ).fetchone()
        if not run:
            return None
        traces   = _get_conn().execute(
            "SELECT seq, node_name, latency_ms, status, log FROM monitor_node_traces WHERE run_id=? ORDER BY seq",
            (run_id,)
        ).fetchall()
        feedback = _get_conn().execute(
            "SELECT restaurant, rating, created_at FROM feedback WHERE run_id=? ORDER BY created_at",
            (run_id,)
        ).fetchall()
    return {**dict(run), "traces": [dict(t) for t in traces], "feedback": [dict(f) for f in feedback]}

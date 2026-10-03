"""
Lightweight SQLite persistence for zone risk history.

Risk history survives backend restarts. Readings are written by
`HeatShieldState` at most once per HISTORY_INTERVAL (default 60 s) for the
whole city -- NOT once per API call or per WebSocket client -- so the file
stays small and the stored series is a genuine, evenly-spaced time series.

Uses only Python's stdlib sqlite3.

The DB location can be overridden with the HEATSHIELD_DB_PATH environment
variable (the test-suite uses this to avoid touching the real file).
"""
import os
import sqlite3
import threading
import time

BASE = os.path.dirname(__file__)
DEFAULT_DB_PATH = os.path.join(BASE, "..", "..", "data", "heatshield_history.db")

_lock = threading.Lock()


def db_path() -> str:
    return os.environ.get("HEATSHIELD_DB_PATH", DEFAULT_DB_PATH)


def _connect():
    conn = sqlite3.connect(db_path(), timeout=5)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(db_path())), exist_ok=True)
    with _lock:
        conn = _connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS risk_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    zone_id TEXT NOT NULL,
                    ts REAL NOT NULL,
                    risk_score REAL NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_zone_ts ON risk_readings (zone_id, ts)")
            conn.commit()
        finally:
            conn.close()


def save_readings(ts: float, scores: dict):
    """Insert one reading per zone ({zone_id: risk_score}) in a single
    transaction, all with the same timestamp. Best-effort: never crashes."""
    try:
        with _lock:
            conn = _connect()
            try:
                conn.executemany(
                    "INSERT INTO risk_readings (zone_id, ts, risk_score) VALUES (?, ?, ?)",
                    [(zid, ts, float(score)) for zid, score in scores.items()],
                )
                conn.commit()
            finally:
                conn.close()
    except Exception as exc:  # noqa: BLE001
        print(f"[db] failed to save readings (non-fatal): {exc}")


def load_recent(zone_id: str, limit: int = 288):
    """Return [(ts, risk_score), ...] for a zone, oldest first."""
    try:
        with _lock:
            conn = _connect()
            try:
                cur = conn.execute(
                    "SELECT ts, risk_score FROM risk_readings WHERE zone_id = ? "
                    "ORDER BY ts DESC LIMIT ?",
                    (zone_id, limit),
                )
                rows = cur.fetchall()
            finally:
                conn.close()
        return list(reversed([(float(t), float(r)) for t, r in rows]))
    except Exception as exc:  # noqa: BLE001
        print(f"[db] failed to load history (non-fatal): {exc}")
        return []


def prune_old(max_age_seconds: float = 7 * 24 * 3600):
    """Drop readings older than max_age_seconds (default 7 days)."""
    try:
        with _lock:
            conn = _connect()
            try:
                conn.execute("DELETE FROM risk_readings WHERE ts < ?", (time.time() - max_age_seconds,))
                conn.commit()
            finally:
                conn.close()
    except Exception as exc:  # noqa: BLE001
        print(f"[db] prune failed (non-fatal): {exc}")

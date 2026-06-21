import sqlite3
import time
import threading
import os
from contextlib import contextmanager

_lock = threading.Lock()


class MetricsStore:
    def __init__(self, db_path="/tmp/metrics.db"):
        self.db_path = db_path
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with _lock, self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS request_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    endpoint TEXT,
                    method TEXT,
                    status_code INTEGER,
                    duration_ms REAL,
                    memory_mb REAL,
                    request_id TEXT
                );
                CREATE TABLE IF NOT EXISTS cache_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    cache_key TEXT,
                    hit INTEGER,
                    endpoint TEXT
                );
                CREATE TABLE IF NOT EXISTS error_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    endpoint TEXT,
                    error_type TEXT,
                    request_id TEXT,
                    message TEXT
                );
                CREATE TABLE IF NOT EXISTS order_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    event_type TEXT,
                    order_id INTEGER
                );
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    alert_type TEXT
                );
            """)

    def _prune(self, conn, table, days=7):
        cutoff = time.time() - days * 86400
        conn.execute(f"DELETE FROM {table} WHERE timestamp < ?", (cutoff,))

    def record_request(self, endpoint, method, status_code, duration_ms, memory_mb, request_id):
        with _lock, self._conn() as conn:
            conn.execute(
                "INSERT INTO request_metrics (timestamp,endpoint,method,status_code,duration_ms,memory_mb,request_id) VALUES (?,?,?,?,?,?,?)",
                (time.time(), endpoint, method, status_code, duration_ms, memory_mb, request_id),
            )
            self._prune(conn, "request_metrics")

    def record_cache(self, cache_key, hit, endpoint=""):
        with _lock, self._conn() as conn:
            conn.execute(
                "INSERT INTO cache_events (timestamp,cache_key,hit,endpoint) VALUES (?,?,?,?)",
                (time.time(), cache_key, 1 if hit else 0, endpoint),
            )
            self._prune(conn, "cache_events")

    def record_error(self, endpoint, error_type, request_id, message):
        with _lock, self._conn() as conn:
            conn.execute(
                "INSERT INTO error_events (timestamp,endpoint,error_type,request_id,message) VALUES (?,?,?,?,?)",
                (time.time(), endpoint, error_type, request_id, message),
            )
            self._prune(conn, "error_events")

    def record_order_event(self, event_type, order_id):
        with _lock, self._conn() as conn:
            conn.execute(
                "INSERT INTO order_events (timestamp,event_type,order_id) VALUES (?,?,?)",
                (time.time(), event_type, order_id),
            )
            self._prune(conn, "order_events")

    def get_summary(self, window_seconds=300):
        cutoff = time.time() - window_seconds
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT endpoint, duration_ms, status_code FROM request_metrics WHERE timestamp > ?",
                (cutoff,),
            ).fetchall()

        if not rows:
            return {"window_seconds": window_seconds, "request_count": 0, "endpoints": {}, "error_rate": 0}

        from collections import defaultdict
        by_endpoint = defaultdict(list)
        errors = 0
        for r in rows:
            by_endpoint[r["endpoint"]].append(r["duration_ms"])
            if r["status_code"] >= 500:
                errors += 1

        def percentile(data, p):
            s = sorted(data)
            idx = int(len(s) * p / 100)
            return s[min(idx, len(s) - 1)]

        endpoints = {}
        for ep, times in by_endpoint.items():
            endpoints[ep] = {
                "count": len(times),
                "p50_ms": round(percentile(times, 50), 2),
                "p95_ms": round(percentile(times, 95), 2),
                "p99_ms": round(percentile(times, 99), 2),
            }

        with self._conn() as conn:
            cache_rows = conn.execute(
                "SELECT hit FROM cache_events WHERE timestamp > ?", (cutoff,)
            ).fetchall()

        cache_hits = sum(1 for r in cache_rows if r["hit"])
        cache_total = len(cache_rows)

        return {
            "window_seconds": window_seconds,
            "request_count": len(rows),
            "error_rate": round(errors / len(rows), 4),
            "endpoints": endpoints,
            "cache_hit_ratio": round(cache_hits / cache_total, 4) if cache_total else None,
        }

    def get_anomalies(self, window_seconds=300):
        summary = self.get_summary(window_seconds)
        anomalies = []

        error_threshold = float(os.environ.get("ALERT_ERROR_RATE_THRESHOLD", "0.10"))
        latency_threshold = int(os.environ.get("ALERT_LATENCY_P95_MS", "2000"))
        spike_threshold = int(os.environ.get("ALERT_ORDER_SPIKE_PER_MINUTE", "10"))

        if summary["error_rate"] > error_threshold:
            anomalies.append({
                "type": "high_error_rate",
                "value": summary["error_rate"],
                "threshold": error_threshold,
                "endpoint": None,
            })

        for ep, stats in summary.get("endpoints", {}).items():
            if stats["p95_ms"] > latency_threshold:
                anomalies.append({
                    "type": "high_latency_p95",
                    "value": stats["p95_ms"],
                    "threshold": latency_threshold,
                    "endpoint": ep,
                })

        cutoff = time.time() - 60
        with self._conn() as conn:
            order_count = conn.execute(
                "SELECT COUNT(*) FROM order_events WHERE timestamp > ? AND event_type='created'",
                (cutoff,),
            ).fetchone()[0]

        if order_count > spike_threshold:
            anomalies.append({
                "type": "order_spike",
                "value": order_count,
                "threshold": spike_threshold,
                "endpoint": "/api/orders",
            })

        return anomalies

    def last_alert_time(self, alert_type):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT MAX(timestamp) FROM alert_history WHERE alert_type=?", (alert_type,)
            ).fetchone()
        return row[0] if row and row[0] else 0

    def record_alert(self, alert_type):
        with _lock, self._conn() as conn:
            conn.execute(
                "INSERT INTO alert_history (timestamp,alert_type) VALUES (?,?)",
                (time.time(), alert_type),
            )


class SimpleCache:
    def __init__(self, default_ttl=60):
        self._store = {}
        self._default_ttl = default_ttl
        self._metrics = None

    def attach_metrics(self, metrics_store):
        self._metrics = metrics_store

    def get(self, key, endpoint=""):
        entry = self._store.get(key)
        if entry and time.time() < entry["expires"]:
            if self._metrics:
                self._metrics.record_cache(key, hit=True, endpoint=endpoint)
            return entry["value"], True
        if self._metrics:
            self._metrics.record_cache(key, hit=False, endpoint=endpoint)
        return None, False

    def set(self, key, value, ttl=None):
        self._store[key] = {
            "value": value,
            "expires": time.time() + (ttl or self._default_ttl),
        }

    def invalidate(self, key):
        self._store.pop(key, None)

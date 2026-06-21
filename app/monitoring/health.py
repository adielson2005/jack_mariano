import time
from datetime import datetime, timezone
from flask import Blueprint, current_app, jsonify

health_bp = Blueprint("health", __name__)
_START_TIME = time.time()


def _human_uptime(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h}h {m}m {s}s"


def check_database(db):
    try:
        start = time.perf_counter()
        db.session.execute(db.text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        try:
            pool_status = str(db.engine.pool.status())
        except Exception:
            pool_status = "unavailable"
        return {"ok": True, "latency_ms": latency_ms, "pool": pool_status}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def check_memory():
    try:
        import psutil, os
        proc = psutil.Process(os.getpid())
        mem = proc.memory_info()
        return {"rss_mb": round(mem.rss / 1024 / 1024, 2), "vms_mb": round(mem.vms / 1024 / 1024, 2)}
    except Exception:
        return {"rss_mb": None, "vms_mb": None}


def check_cpu():
    try:
        import psutil, os
        proc = psutil.Process(os.getpid())
        return {"percent": proc.cpu_percent(interval=0.1)}
    except Exception:
        return {"percent": None}


@health_bp.route("/health")
def health():
    from app import db

    uptime_secs = time.time() - _START_TIME
    db_status = check_database(db)
    memory = check_memory()
    cpu = check_cpu()

    metrics_store = current_app.extensions.get("metrics")
    anomalies = metrics_store.get_anomalies() if metrics_store else []
    summary = metrics_store.get_summary() if metrics_store else {}

    status = "ok" if db_status["ok"] else "degraded"
    http_code = 200 if db_status["ok"] else 503

    payload = {
        "status": status,
        "version": "v20",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime": {"seconds": round(uptime_secs, 1), "human": _human_uptime(uptime_secs)},
        "db": db_status,
        "memory": memory,
        "cpu": cpu,
        "metrics_summary": summary,
        "anomalies": anomalies,
    }

    return jsonify(payload), http_code

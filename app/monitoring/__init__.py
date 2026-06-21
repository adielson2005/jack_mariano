import time
import os
import traceback

from flask import g, request, jsonify

from app.monitoring.logger import configure_logging, get_logger
from app.monitoring.request_context import RequestContextMiddleware, generate_request_id
from app.monitoring.metrics import MetricsStore, SimpleCache
from app.monitoring.alerts import AlertManager, start_background_checker
from app.monitoring.health import health_bp

logger = get_logger("monitoring")

# Shared in-process cache accessible from route modules
catalog_cache = SimpleCache(default_ttl=120)


def init_monitoring(app):
    # 1. Structured JSON logging
    configure_logging(app)

    # 2. Metrics store (SQLite)
    db_path = app.config.get("METRICS_DB_PATH", os.environ.get("METRICS_DB_PATH", "/tmp/metrics.db"))
    metrics = MetricsStore(db_path)
    app.extensions["metrics"] = metrics
    catalog_cache.attach_metrics(metrics)

    # 3. DB query logging
    from app.monitoring.query_logger import register_query_listeners
    from app import db
    register_query_listeners(db)

    # 4. Request ID injection via WSGI middleware
    app.wsgi_app = RequestContextMiddleware(app.wsgi_app, app)

    # 5. Before-request: populate g.request_id and start timer
    @app.before_request
    def _before():
        g.request_id = request.environ.get("X_REQUEST_ID", generate_request_id())
        g._req_start = time.perf_counter()
        logger.debug(
            "request.in",
            extra_fields={"method": request.method, "path": request.path, "ip": request.remote_addr},
        )

    # 6. After-request: record metrics + structured access log
    @app.after_request
    def _after(response):
        duration_ms = round((time.perf_counter() - getattr(g, "_req_start", time.perf_counter())) * 1000, 2)
        memory_mb = _get_memory_mb()
        endpoint = request.endpoint or request.path
        metrics.record_request(endpoint, request.method, response.status_code, duration_ms, memory_mb, g.request_id)
        response.headers["X-Request-ID"] = g.request_id
        logger.info(
            "request.out",
            extra_fields={
                "status": response.status_code,
                "duration_ms": duration_ms,
                "memory_mb": memory_mb,
            },
        )
        return response

    # 7. Global error handler: full stack trace + context (só erros 5xx reais)
    @app.errorhandler(Exception)
    def _handle_error(exc):
        from werkzeug.exceptions import HTTPException
        from app.monitoring.request_context import get_request_id
        # Deixa erros HTTP (404, 405, etc.) passarem para os handlers padrão do Flask
        if isinstance(exc, HTTPException):
            return exc
        metrics.record_error(
            endpoint=request.endpoint or request.path,
            error_type=type(exc).__name__,
            request_id=get_request_id(),
            message=str(exc),
        )
        logger.error(
            "unhandled_exception",
            exc_info=True,
            extra_fields={
                "error_type": type(exc).__name__,
                "path": request.path,
                "method": request.method,
            },
        )
        return jsonify({"error": "internal_server_error", "request_id": get_request_id()}), 500

    # 8. Health check blueprint (replaces the one in run.py)
    app.register_blueprint(health_bp)

    # 9. Alerts background checker
    alert_manager = AlertManager(metrics)
    start_background_checker(alert_manager, interval_seconds=60)

    logger.info("monitoring.initialized", extra_fields={"metrics_db": db_path})


def _get_memory_mb():
    try:
        import psutil, os as _os
        return round(psutil.Process(_os.getpid()).memory_info().rss / 1024 / 1024, 2)
    except Exception:
        return None

import time
import os
from app.monitoring.logger import get_logger
from app.monitoring.request_context import get_request_id

logger = get_logger("db.query")
_SLOW_MS = int(os.environ.get("SLOW_QUERY_MS", "100"))


def register_query_listeners(db):
    from sqlalchemy import event

    @event.listens_for(db.engine, "before_cursor_execute")
    def before_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info["_query_start"] = time.perf_counter()

    @event.listens_for(db.engine, "after_cursor_execute")
    def after_execute(conn, cursor, statement, parameters, context, executemany):
        start = conn.info.pop("_query_start", None)
        if start is None:
            return
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        truncated = statement[:500] if len(statement) > 500 else statement
        log_data = {
            "query": truncated,
            "duration_ms": duration_ms,
            "request_id": get_request_id(),
        }
        if duration_ms >= _SLOW_MS:
            logger.warning("slow_query", extra_fields=log_data)
        else:
            logger.debug("db_query", extra_fields=log_data)

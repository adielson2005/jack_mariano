import logging
import json
import traceback
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record):
        try:
            from flask import g, request
            request_id = getattr(g, "request_id", "no-request-id")
            method = request.method
            path = request.path
            ip = request.remote_addr
        except RuntimeError:
            request_id = "no-request-id"
            method = None
            path = None
            ip = None

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id,
        }

        if method:
            entry["method"] = method
        if path:
            entry["path"] = path
        if ip:
            entry["ip"] = ip

        duration_ms = getattr(record, "duration_ms", None)
        if duration_ms is not None:
            entry["duration_ms"] = duration_ms

        extra = getattr(record, "extra_fields", None)
        if extra:
            entry["extra"] = extra

        if record.exc_info:
            entry["exc_info"] = traceback.format_exception(*record.exc_info)

        return json.dumps(entry, ensure_ascii=False)


class ContextLogger(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra_fields = kwargs.pop("extra_fields", {})
        kwargs.setdefault("extra", {})["extra_fields"] = extra_fields
        return msg, kwargs


def configure_logging(app):
    import os
    level_name = os.environ.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    formatter = JSONFormatter()

    root = logging.getLogger()
    root.setLevel(level)
    for handler in root.handlers:
        handler.setFormatter(formatter)
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root.addHandler(handler)

    for name in ("gunicorn.error", "gunicorn.access"):
        glog = logging.getLogger(name)
        glog.setLevel(level)
        for h in glog.handlers:
            h.setFormatter(formatter)

    app.logger.setLevel(level)


def get_logger(name):
    return ContextLogger(logging.getLogger(name), {})

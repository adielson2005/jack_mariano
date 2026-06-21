import os
import time
import threading
import urllib.request
import urllib.error
from app.monitoring.logger import get_logger

logger = get_logger("alerts")


class AlertManager:
    def __init__(self, metrics_store):
        self._metrics = metrics_store
        self._webhook = os.environ.get("ALERT_WEBHOOK_URL", "")
        self._cooldown = int(os.environ.get("ALERT_COOLDOWN_SECONDS", "300"))

    def check_and_fire(self):
        try:
            anomalies = self._metrics.get_anomalies()
            for anomaly in anomalies:
                self._maybe_fire(anomaly)
        except Exception as exc:
            logger.error("alert_check_failed", extra_fields={"error": str(exc)})

    def _maybe_fire(self, anomaly):
        alert_type = anomaly["type"]
        last = self._metrics.last_alert_time(alert_type)
        if time.time() - last < self._cooldown:
            return
        self._metrics.record_alert(alert_type)
        logger.critical(
            "anomaly_detected",
            extra_fields=anomaly,
        )
        if self._webhook:
            self._send_webhook(anomaly)

    def _send_webhook(self, anomaly):
        try:
            body = (
                f"[jack_mariano] ALERT: {anomaly['type']}\n"
                f"Value: {anomaly['value']} | Threshold: {anomaly['threshold']}\n"
                f"Endpoint: {anomaly.get('endpoint') or 'global'}"
            ).encode()
            req = urllib.request.Request(self._webhook, data=body, method="POST")
            req.add_header("Content-Type", "text/plain")
            urllib.request.urlopen(req, timeout=5)
        except urllib.error.URLError as exc:
            logger.warning("webhook_failed", extra_fields={"error": str(exc)})


def start_background_checker(alert_manager, interval_seconds=60):
    def _loop():
        while True:
            time.sleep(interval_seconds)
            alert_manager.check_and_fire()

    t = threading.Thread(target=_loop, daemon=True, name="alert-checker")
    t.start()
    return t

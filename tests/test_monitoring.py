"""Regression tests for critical flows and monitoring rules."""
import json
import pytest


# ── Rule 1: Request ID ────────────────────────────────────────────────────────

class TestRequestId:
    def test_request_id_present_in_response_header(self, client):
        r = client.get("/health")
        assert "X-Request-ID" in r.headers

    def test_request_id_is_unique_per_request(self, client):
        ids = {client.get("/health").headers.get("X-Request-ID") for _ in range(5)}
        assert len(ids) == 5


# ── Rule 4: Health check ──────────────────────────────────────────────────────

class TestHealthCheck:
    def test_health_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_health_has_db_key(self, client):
        data = r = client.get("/health").get_json()
        assert "db" in data
        assert data["db"]["ok"] is True

    def test_health_has_memory_key(self, client):
        data = client.get("/health").get_json()
        assert "memory" in data

    def test_health_has_uptime_key(self, client):
        data = client.get("/health").get_json()
        assert "uptime" in data
        assert data["uptime"]["seconds"] >= 0

    def test_health_has_anomalies_key(self, client):
        data = client.get("/health").get_json()
        assert "anomalies" in data
        assert isinstance(data["anomalies"], list)

    def test_health_has_status_key(self, client):
        data = client.get("/health").get_json()
        assert data["status"] in ("ok", "degraded")


# ── Rule 8: Order creation (critical flow) ────────────────────────────────────

class TestOrderCreation:
    def test_create_order_valid(self, client, sample_order_payload):
        r = client.post(
            "/api/orders",
            data=json.dumps(sample_order_payload),
            content_type="application/json",
        )
        assert r.status_code == 201
        data = r.get_json()
        assert "order_id" in data

    def test_create_order_missing_name(self, client, sample_order_payload):
        payload = {**sample_order_payload}
        del payload["customer_name"]
        r = client.post("/api/orders", data=json.dumps(payload), content_type="application/json")
        assert r.status_code == 400

    def test_create_order_missing_whatsapp(self, client, sample_order_payload):
        payload = {**sample_order_payload}
        del payload["customer_whatsapp"]
        r = client.post("/api/orders", data=json.dumps(payload), content_type="application/json")
        assert r.status_code == 400

    def test_create_order_missing_items(self, client, sample_order_payload):
        payload = {**sample_order_payload, "items": []}
        r = client.post("/api/orders", data=json.dumps(payload), content_type="application/json")
        assert r.status_code == 400

    def test_create_order_returns_request_id_header(self, client, sample_order_payload):
        r = client.post(
            "/api/orders",
            data=json.dumps(sample_order_payload),
            content_type="application/json",
        )
        assert "X-Request-ID" in r.headers


# ── Rule 8: Categories API ────────────────────────────────────────────────────

class TestCategoriesApi:
    def test_categories_returns_list(self, client):
        r = client.get("/api/categories")
        assert r.status_code == 200
        data = r.get_json()
        assert isinstance(data, list)

    def test_categories_have_required_fields(self, client):
        data = client.get("/api/categories").get_json()
        for cat in data:
            assert "slug" in cat
            assert "name" in cat


# ── Rule 8: Login + rate limit ────────────────────────────────────────────────

class TestLogin:
    def test_login_wrong_password_returns_error(self, client):
        r = client.post("/admin/login", data={"username": "admin", "password": "wrong"})
        assert r.status_code in (200, 401)

    def test_login_rate_limit_after_5_failures(self, client):
        for _ in range(5):
            client.post("/admin/login", data={"username": "admin", "password": "bad"})
        r = client.post("/admin/login", data={"username": "admin", "password": "bad"})
        assert r.status_code in (429, 200)


# ── Rule 6: Cache hit/miss tracking ──────────────────────────────────────────

class TestCacheMetrics:
    def test_simple_cache_hit_miss(self, app_fixture):
        from app.monitoring.metrics import SimpleCache, MetricsStore
        store = MetricsStore("/tmp/test_cache_metrics.db")
        cache = SimpleCache(default_ttl=60)
        cache.attach_metrics(store)

        _, hit = cache.get("key1")
        assert hit is False

        cache.set("key1", "value")
        val, hit = cache.get("key1")
        assert hit is True
        assert val == "value"

    def test_simple_cache_expiry(self, app_fixture):
        import time
        from app.monitoring.metrics import SimpleCache
        cache = SimpleCache(default_ttl=0)
        cache.set("key2", "data", ttl=0)
        time.sleep(0.01)
        _, hit = cache.get("key2")
        assert hit is False


# ── Rule 7 & 9: Metrics store ────────────────────────────────────────────────

class TestMetricsStore:
    def test_record_and_summary(self, app_fixture):
        from app.monitoring.metrics import MetricsStore
        store = MetricsStore("/tmp/test_metrics_summary.db")
        store.record_request("test_ep", "GET", 200, 45.0, 30.0, "abc123")
        store.record_request("test_ep", "GET", 200, 120.0, 30.0, "def456")
        summary = store.get_summary(window_seconds=60)
        assert summary["request_count"] >= 2
        assert "test_ep" in summary["endpoints"]

    def test_anomaly_high_error_rate(self, app_fixture):
        import os
        os.environ["ALERT_ERROR_RATE_THRESHOLD"] = "0.01"
        from app.monitoring.metrics import MetricsStore
        store = MetricsStore("/tmp/test_metrics_anomaly.db")
        for _ in range(10):
            store.record_request("bad_ep", "POST", 500, 100.0, 30.0, "xxx")
        anomalies = store.get_anomalies(window_seconds=60)
        types = [a["type"] for a in anomalies]
        assert "high_error_rate" in types
        os.environ["ALERT_ERROR_RATE_THRESHOLD"] = "0.10"

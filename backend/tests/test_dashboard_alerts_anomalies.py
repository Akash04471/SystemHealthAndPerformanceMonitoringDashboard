from datetime import datetime

import pytest


class ScriptedCursor:
    def __init__(self, script):
        self.script = list(script)
        self.current_step = None

    def execute(self, query, params=None):
        if not self.script:
            raise AssertionError(f"Unexpected query executed: {query}")

        self.current_step = self.script.pop(0)
        expected_fragment = self.current_step.get("contains")
        if expected_fragment:
            normalized_query = " ".join(query.split())
            assert expected_fragment in normalized_query

        if "params" in self.current_step:
            assert params == self.current_step["params"]

    def fetchone(self):
        return self.current_step.get("one")

    def fetchall(self):
        return self.current_step.get("all", [])

    def close(self):
        return None


class ScriptedConnection:
    def __init__(self, script):
        self.cursor_instance = ScriptedCursor(script)
        self.committed = False

    def cursor(self, dictionary=True):
        assert dictionary is True
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def close(self):
        return None


def test_dashboard_summary_returns_aggregates(client, auth_headers, monkeypatch):
    from backend.app.api.routes import dashboard

    script = [
        {"contains": "COUNT(*) AS total FROM alerts", "one": {"total": 3}},
        {
            "contains": "SELECT severity, COUNT(*) AS total",
            "all": [
                {"severity": "high", "total": 2},
                {"severity": "critical", "total": 1},
            ],
        },
        {
            "contains": "COUNT(*) AS total FROM anomalies",
            "params": (datetime(2026, 1, 1, 0, 0, 0), 24),
            "one": {"total": 5},
        },
        {
            "contains": "SELECT s.service_key, MAX(m.ts) AS last_ingestion_at",
            "all": [{"service_key": "svc-api", "last_ingestion_at": None}],
        },
    ]
    conn = ScriptedConnection(script)

    monkeypatch.setattr(dashboard, "ensure_schema", lambda: None)
    monkeypatch.setattr(dashboard, "get_connection", lambda: conn)
    monkeypatch.setattr(dashboard, "now_utc_naive", lambda: datetime(2026, 1, 1, 0, 0, 0))

    response = client.get("/api/v1/dashboard/summary?window_hours=24", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["open_alert_count"] == 3
    assert payload["recent_anomaly_count"] == 5
    assert payload["alerts_by_severity"]["critical"] == 1
    assert payload["alerts_by_severity"]["high"] == 2
    assert payload["last_ingestion_by_service"][0]["service_key"] == "svc-api"


def test_list_alerts_applies_status_and_service_filters(client, auth_headers, monkeypatch):
    from backend.app.api.routes import alerts

    script = [
        {
            "contains": "WHERE 1 = 1 AND a.status = %s AND s.service_key = %s ORDER BY a.opened_at DESC LIMIT %s",
            "params": ("open", "svc-api", 10),
            "all": [
                {
                    "id": 7,
                    "service_key": "svc-api",
                    "source_type": "anomaly",
                    "status": "open",
                    "severity": "high",
                    "title": "CPU spike",
                    "description": "Detected anomaly",
                    "opened_at": "2026-01-01T00:00:00",
                    "acknowledged_at": None,
                    "resolved_at": None,
                    "cooldown_until": None,
                }
            ],
        }
    ]
    conn = ScriptedConnection(script)

    monkeypatch.setattr(alerts, "ensure_schema", lambda: None)
    monkeypatch.setattr(alerts, "get_connection", lambda: conn)

    response = client.get(
        "/api/v1/alerts?status=open&service_key=svc-api&limit=10",
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["service_key"] == "svc-api"


def test_resolve_alert_marks_resolved_and_commits(client, auth_headers, monkeypatch):
    from backend.app.api.routes import alerts

    script = [
        {"contains": "SELECT * FROM alerts WHERE id = %s", "params": (3,), "one": {"id": 3, "status": "open"}},
        {"contains": "UPDATE alerts SET status = 'resolved', resolved_at = %s WHERE id = %s"},
        {"contains": "INSERT INTO alert_events"},
    ]
    conn = ScriptedConnection(script)

    monkeypatch.setattr(alerts, "ensure_schema", lambda: None)
    monkeypatch.setattr(alerts, "get_connection", lambda: conn)
    monkeypatch.setattr(alerts, "now_utc_naive", lambda: datetime(2026, 1, 1, 0, 0, 0))

    response = client.post("/api/v1/alerts/3/resolve", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"status": "resolved", "alert_id": 3}
    assert conn.committed is True


def test_list_anomalies_filters_by_service_key(client, auth_headers, monkeypatch):
    from backend.app.api.routes import anomalies

    script = [
        {
            "contains": "WHERE s.service_key = %s ORDER BY a.ts DESC LIMIT %s",
            "params": ("svc-db", 5),
            "all": [
                {
                    "id": 99,
                    "service_key": "svc-db",
                    "metric_name": "disk_percent",
                    "ts": "2026-01-01T00:00:00",
                    "method": "zscore",
                    "score": 2.2,
                    "severity": "medium",
                    "details_json": {},
                }
            ],
        }
    ]
    conn = ScriptedConnection(script)

    monkeypatch.setattr(anomalies, "ensure_schema", lambda: None)
    monkeypatch.setattr(anomalies, "get_connection", lambda: conn)

    response = client.get("/api/v1/anomalies?service_key=svc-db&limit=5", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["service_key"] == "svc-db"

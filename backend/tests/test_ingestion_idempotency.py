import uuid
from datetime import datetime, timezone


def _identity_payload() -> dict:
    return {
        "service_key": "test-collector-service",
        "host_name": "test-host",
        "environment": "testing",
    }


def _metric_payload() -> dict:
    return {
        "identity": _identity_payload(),
        "points": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cpu_percent": 10.5,
                "memory_percent": 22.3,
                "disk_percent": 33.7,
                "uptime_seconds": 12345,
            }
        ],
    }


def _logs_payload() -> dict:
    return {
        "identity": _identity_payload(),
        "records": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "message": "Test log entry for idempotency",
            }
        ],
    }


def test_metrics_ingestion_is_idempotent(client, auth_headers):
    idempotency_key = str(uuid.uuid4())
    headers = {**auth_headers, "Idempotency-Key": idempotency_key}
    payload = _metric_payload()

    first_response = client.post("/api/v1/ingest/metrics", json=payload, headers=headers)
    assert first_response.status_code == 200
    assert first_response.json()["received_points"] == 1
    assert first_response.json()["service_key"] == payload["identity"]["service_key"]

    second_response = client.post("/api/v1/ingest/metrics", json=payload, headers=headers)
    assert second_response.status_code == 200
    assert second_response.json()["received_points"] == 0
    assert second_response.json().get("duplication") == "idempotent request"


def test_logs_ingestion_is_idempotent(client, auth_headers):
    idempotency_key = str(uuid.uuid4())
    headers = {**auth_headers, "Idempotency-Key": idempotency_key}
    payload = _logs_payload()

    first_response = client.post("/api/v1/ingest/logs", json=payload, headers=headers)
    assert first_response.status_code == 200
    assert first_response.json()["received_records"] == 1
    assert first_response.json()["service_key"] == payload["identity"]["service_key"]

    second_response = client.post("/api/v1/ingest/logs", json=payload, headers=headers)
    assert second_response.status_code == 200
    assert second_response.json()["received_records"] == 0
    assert second_response.json().get("duplication") == "idempotent request"

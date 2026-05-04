from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from ...api.dependencies.auth import get_current_claims
from ...core.db import ensure_schema, get_connection, now_utc_naive
from ...services.anomaly import run_zscore_detection

router = APIRouter()


class ServiceIdentity(BaseModel):
    service_key: str = Field(min_length=2, max_length=100)
    host_name: str = Field(min_length=1, max_length=255)
    environment: str = Field(min_length=1, max_length=50)


class MetricPoint(BaseModel):
    timestamp: datetime
    cpu_percent: float = Field(ge=0, le=100)
    memory_percent: float = Field(ge=0, le=100)
    disk_percent: float = Field(ge=0, le=100)
    uptime_seconds: int = Field(ge=0)


class MetricsIngestRequest(BaseModel):
    identity: ServiceIdentity
    points: list[MetricPoint]


class LogRecord(BaseModel):
    timestamp: datetime
    level: str = Field(default="INFO", min_length=2, max_length=16)
    message: str = Field(min_length=1)


class LogsIngestRequest(BaseModel):
    identity: ServiceIdentity
    records: list[LogRecord]


def _to_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone().replace(tzinfo=None)


def _upsert_service(identity: ServiceIdentity) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO services (service_key, host_name, environment, last_seen_at)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              host_name = VALUES(host_name),
              environment = VALUES(environment),
              last_seen_at = VALUES(last_seen_at)
            """,
            (identity.service_key, identity.host_name, identity.environment, now_utc_naive()),
        )
        conn.commit()
        cursor.execute("SELECT id FROM services WHERE service_key = %s", (identity.service_key,))
        row = cursor.fetchone()
        return int(row[0])
    finally:
        cursor.close()
        conn.close()


def _is_duplicate_request(service_id: int, endpoint: str, idempotency_key: str, cursor) -> bool:
    cursor.execute(
        "SELECT id FROM ingestion_idempotency WHERE idempotency_key = %s AND endpoint = %s AND service_id = %s",
        (idempotency_key, endpoint, service_id),
    )
    return cursor.fetchone() is not None


def _store_idempotency_key(service_id: int, endpoint: str, idempotency_key: str, cursor):
    cursor.execute(
        "INSERT INTO ingestion_idempotency (service_id, endpoint, idempotency_key) VALUES (%s, %s, %s)",
        (service_id, endpoint, idempotency_key),
    )


@router.post("/metrics")
def ingest_metrics(
    payload: MetricsIngestRequest,
    _claims: dict = Depends(get_current_claims),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    ensure_schema()
    service_id = _upsert_service(payload.identity)
    endpoint = "metrics"

    conn = get_connection()
    cursor = conn.cursor()
    try:
        if idempotency_key:
            if _is_duplicate_request(service_id, endpoint, idempotency_key, cursor):
                return {
                    "status": "accepted",
                    "received_points": 0,
                    "service_key": payload.identity.service_key,
                    "service_id": service_id,
                    "duplication": "idempotent request",
                }

        values = [
            (
                service_id,
                _to_naive_utc(point.timestamp),
                point.cpu_percent,
                point.memory_percent,
                point.disk_percent,
                point.uptime_seconds,
            )
            for point in payload.points
        ]
        if values:
            cursor.executemany(
                """
                INSERT INTO metrics (service_id, ts, cpu_percent, memory_percent, disk_percent, uptime_seconds)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                values,
            )
            if idempotency_key:
                _store_idempotency_key(service_id, endpoint, idempotency_key, cursor)
            conn.commit()
    finally:
        cursor.close()
        conn.close()

    detection = run_zscore_detection(service_id=service_id, service_key=payload.identity.service_key)

    return {
        "status": "accepted",
        "received_points": len(payload.points),
        "service_key": payload.identity.service_key,
        "service_id": service_id,
        "detection": detection,
    }


@router.post("/logs")
def ingest_logs(
    payload: LogsIngestRequest,
    _claims: dict = Depends(get_current_claims),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    ensure_schema()
    service_id = _upsert_service(payload.identity)
    endpoint = "logs"

    conn = get_connection()
    cursor = conn.cursor()
    try:
        if idempotency_key:
            if _is_duplicate_request(service_id, endpoint, idempotency_key, cursor):
                return {
                    "status": "accepted",
                    "received_records": 0,
                    "service_key": payload.identity.service_key,
                    "service_id": service_id,
                    "duplication": "idempotent request",
                }

        values = [
            (
                service_id,
                _to_naive_utc(record.timestamp),
                record.level.upper(),
                record.message,
            )
            for record in payload.records
        ]
        if values:
            cursor.executemany(
                """
                INSERT INTO logs (service_id, ts, level, message)
                VALUES (%s, %s, %s, %s)
                """,
                values,
            )
            if idempotency_key:
                _store_idempotency_key(service_id, endpoint, idempotency_key, cursor)
            conn.commit()
    finally:
        cursor.close()
        conn.close()

    return {
        "status": "accepted",
        "received_records": len(payload.records),
        "service_key": payload.identity.service_key,
        "service_id": service_id,
    }


@router.post("/services/register")
def register_service(identity: ServiceIdentity, _claims: dict = Depends(get_current_claims)) -> dict:
    ensure_schema()
    service_id = _upsert_service(identity)

    return {
        "status": "registered",
        "service_id": service_id,
        "service_key": identity.service_key,
        "host_name": identity.host_name,
        "environment": identity.environment,
    }

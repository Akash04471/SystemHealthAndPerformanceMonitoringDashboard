from fastapi import APIRouter, Depends, Query

from ...api.dependencies.auth import get_current_claims
from ...core.db import ensure_schema, get_connection, now_utc_naive

router = APIRouter()


@router.get("/summary")
def dashboard_summary(
    window_hours: int = Query(default=24, ge=1, le=168),
    _claims: dict = Depends(get_current_claims),
) -> dict:
    ensure_schema()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM alerts WHERE status = 'open'")
        open_alert_count = int(cursor.fetchone()["total"])

        cursor.execute(
            """
            SELECT severity, COUNT(*) AS total
            FROM alerts
            WHERE status = 'open'
            GROUP BY severity
            """
        )
        severity_rows = cursor.fetchall()
        alerts_by_severity = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0,
        }
        for row in severity_rows:
            alerts_by_severity[row["severity"]] = int(row["total"])

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM anomalies
            WHERE ts >= DATE_SUB(%s, INTERVAL %s HOUR)
            """,
            (now_utc_naive(), window_hours),
        )
        recent_anomaly_count = int(cursor.fetchone()["total"])

        cursor.execute(
            """
            SELECT s.service_key, MAX(m.ts) AS last_ingestion_at
            FROM services s
            LEFT JOIN metrics m ON m.service_id = s.id
            GROUP BY s.service_key
            ORDER BY s.service_key ASC
            """
        )
        ingestion_rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return {
        "window_hours": window_hours,
        "open_alert_count": open_alert_count,
        "alerts_by_severity": alerts_by_severity,
        "recent_anomaly_count": recent_anomaly_count,
        "last_ingestion_by_service": ingestion_rows,
    }

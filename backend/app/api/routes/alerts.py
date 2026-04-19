from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...api.dependencies.auth import get_current_claims
from ...core.db import ensure_schema, get_connection, now_utc_naive

router = APIRouter()


def _fetch_alert_or_404(cursor, alert_id: int) -> dict:
    cursor.execute("SELECT * FROM alerts WHERE id = %s", (alert_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return row


@router.get("")
def list_alerts(
    status_filter: str | None = Query(default=None, alias="status"),
    service_key: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    _claims: dict = Depends(get_current_claims),
) -> dict:
    ensure_schema()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT a.id, s.service_key, a.source_type, a.status, a.severity, a.title, a.description,
                   a.opened_at, a.acknowledged_at, a.resolved_at, a.cooldown_until
            FROM alerts a
            JOIN services s ON a.service_id = s.id
            WHERE 1 = 1
        """
        params: list = []

        if status_filter:
            query += " AND a.status = %s"
            params.append(status_filter)

        if service_key:
            query += " AND s.service_key = %s"
            params.append(service_key)

        query += " ORDER BY a.opened_at DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return {"count": len(rows), "items": rows}


@router.post("/{alert_id}/ack")
def acknowledge_alert(alert_id: int, claims: dict = Depends(get_current_claims)) -> dict:
    ensure_schema()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        event_time = now_utc_naive()
        alert = _fetch_alert_or_404(cursor, alert_id)
        if alert["status"] == "resolved":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resolved alert cannot be acknowledged")

        cursor.execute(
            """
            UPDATE alerts
            SET status = 'acknowledged', acknowledged_at = %s
            WHERE id = %s
            """,
            (event_time, alert_id),
        )
        cursor.execute(
            """
            INSERT INTO alert_events (alert_id, event_type, actor_type, event_ts, details_json)
            VALUES (%s, 'acknowledged', 'user', %s, JSON_OBJECT('by', %s))
            """,
            (alert_id, event_time, str(claims.get("sub", "unknown"))),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return {"status": "acknowledged", "alert_id": alert_id}


@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int, claims: dict = Depends(get_current_claims)) -> dict:
    ensure_schema()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        event_time = now_utc_naive()
        _ = _fetch_alert_or_404(cursor, alert_id)

        cursor.execute(
            """
            UPDATE alerts
            SET status = 'resolved', resolved_at = %s
            WHERE id = %s
            """,
            (event_time, alert_id),
        )
        cursor.execute(
            """
            INSERT INTO alert_events (alert_id, event_type, actor_type, event_ts, details_json)
            VALUES (%s, 'resolved', 'user', %s, JSON_OBJECT('by', %s))
            """,
            (alert_id, event_time, str(claims.get("sub", "unknown"))),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

    return {"status": "resolved", "alert_id": alert_id}


@router.get("/{alert_id}/events")
def list_alert_events(alert_id: int, _claims: dict = Depends(get_current_claims)) -> dict:
    ensure_schema()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT id, event_type, actor_type, actor_id, event_ts, details_json
            FROM alert_events
            WHERE alert_id = %s
            ORDER BY event_ts DESC
            """,
            (alert_id,),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return {"count": len(rows), "items": rows}

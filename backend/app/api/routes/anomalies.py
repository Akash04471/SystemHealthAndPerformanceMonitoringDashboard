from fastapi import APIRouter, Depends, Query

from ...api.dependencies.auth import get_current_claims
from ...core.db import ensure_schema, get_connection

router = APIRouter()


@router.get("")
def list_anomalies(
    service_key: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    _claims: dict = Depends(get_current_claims),
) -> dict:
    ensure_schema()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT a.id, s.service_key, a.metric_name, a.ts, a.method, a.score, a.severity, a.details_json
            FROM anomalies a
            JOIN services s ON a.service_id = s.id
        """
        params: tuple = ()

        if service_key:
            query += " WHERE s.service_key = %s"
            params = (service_key,)

        query += " ORDER BY a.ts DESC LIMIT %s"
        params = params + (limit,)

        cursor.execute(query, params)
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return {"count": len(rows), "items": rows}

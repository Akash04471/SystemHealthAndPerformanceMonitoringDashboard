from fastapi import APIRouter, Depends, Query

from ...api.dependencies.auth import get_current_claims
from ...core.db import ensure_schema, get_connection

router = APIRouter()


@router.get("")
def list_metrics(
    service_key: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    _claims: dict = Depends(get_current_claims),
) -> dict:
    ensure_schema()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        base_query = """
            SELECT s.service_key, m.ts, m.cpu_percent, m.memory_percent, m.disk_percent, m.uptime_seconds
            FROM metrics m
            JOIN services s ON m.service_id = s.id
        """
        params: tuple = ()

        if service_key:
            base_query += " WHERE s.service_key = %s"
            params = (service_key,)

        base_query += " ORDER BY m.ts DESC LIMIT %s"
        params = params + (limit,)

        cursor.execute(base_query, params)
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return {
        "count": len(rows),
        "items": rows,
    }

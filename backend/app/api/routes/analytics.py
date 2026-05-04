from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
import io
import csv
from datetime import timedelta

from ...api.dependencies.auth import get_current_claims
from ...core.db import get_connection, now_utc_naive

router = APIRouter()

@router.get("/history")
def get_metrics_history(
    days: int = Query(default=7, ge=1, le=30),
    _claims: dict = Depends(get_current_claims),
) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Group by hour to prevent sending too much data
        cursor.execute(
            """
            SELECT 
                DATE_FORMAT(ts, '%Y-%m-%d %H:00:00') as hour,
                AVG(cpu_percent) as avg_cpu,
                AVG(memory_percent) as avg_memory,
                AVG(disk_percent) as avg_disk
            FROM metrics
            WHERE ts >= DATE_SUB(%s, INTERVAL %s DAY)
            GROUP BY hour
            ORDER BY hour ASC
            """,
            (now_utc_naive(), days),
        )
        history = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    return {"days": days, "points": history}

@router.get("/report/csv")
def export_csv_report(_claims: dict = Depends(get_current_claims)):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT s.service_key, m.ts, m.cpu_percent, m.memory_percent, m.disk_percent
            FROM metrics m
            JOIN services s ON m.service_id = s.id
            ORDER BY m.ts DESC
            LIMIT 1000
            """
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["service_key", "ts", "cpu_percent", "memory_percent", "disk_percent"])
    writer.writeheader()
    writer.writerows(rows)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=system_health_report.csv"}
    )

@router.get("/predictions")
def get_resource_predictions(_claims: dict = Depends(get_current_claims)) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Basic prediction logic: Compare last 24h average with previous 24h average
        # to see if it's rising and estimate when it hits 100%
        cursor.execute(
            """
            SELECT 
                AVG(disk_percent) as avg_now,
                (SELECT AVG(disk_percent) FROM metrics WHERE ts BETWEEN DATE_SUB(NOW(), INTERVAL 48 HOUR) AND DATE_SUB(NOW(), INTERVAL 24 HOUR)) as avg_before
            FROM metrics 
            WHERE ts >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """
        )
        data = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    predictions = []
    if data and data["avg_now"] and data["avg_before"]:
        growth_rate = data["avg_now"] - data["avg_before"]
        if growth_rate > 0:
            remaining = 100 - data["avg_now"]
            days_left = remaining / (growth_rate * 1) # Simple linear model
            predictions.append({
                "metric": "Disk Usage",
                "trend": "rising",
                "days_until_exhaustion": round(days_left, 1),
                "severity": "high" if days_left < 7 else "medium"
            })
        else:
            predictions.append({
                "metric": "Disk Usage",
                "trend": "stable",
                "days_until_exhaustion": None,
                "severity": "low"
            })

    return {"predictions": predictions}

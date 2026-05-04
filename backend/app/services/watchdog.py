import logging
import asyncio
from datetime import datetime, timedelta
from ..core.db import get_connection, now_utc_naive

async def start_watchdog():
    """
    Background task to monitor if services are still sending metrics.
    If a service hasn't sent data for > 5 minutes, it creates an alert.
    """
    logging.info("Starting Service Watchdog...")
    while True:
        try:
            check_agent_heartbeats()
        except Exception as e:
            logging.error(f"Watchdog error: {e}")
        
        # Run every 60 seconds
        await asyncio.sleep(60)

def check_agent_heartbeats():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # 1. Find services that were online but haven't sent data recently
        # and don't already have an open 'Agent Offline' alert
        cursor.execute(
            """
            SELECT s.id, s.service_key, s.last_seen_at
            FROM services s
            LEFT JOIN alerts a ON s.id = a.service_id AND a.title = 'Agent Offline' AND a.status = 'open'
            WHERE s.last_seen_at < DATE_SUB(%s, INTERVAL 5 MINUTE)
              AND a.id IS NULL
            """,
            (now_utc_naive(),)
        )
        offline_services = cursor.fetchall()

        for service in offline_services:
            logging.warning(f"Service {service['service_key']} detected as OFFLINE (Last seen: {service['last_seen_at']})")
            
            # Create a system alert
            cursor.execute(
                """
                INSERT INTO alerts (service_id, title, description, severity, status, source_type, opened_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    service['id'],
                    "Agent Offline",
                    f"The collector agent for {service['service_key']} has stopped sending heartbeats.",
                    "high",
                    "open",
                    "metric",
                    now_utc_naive()
                )
            )
        
        if offline_services:
            conn.commit()

    finally:
        cursor.close()
        conn.close()

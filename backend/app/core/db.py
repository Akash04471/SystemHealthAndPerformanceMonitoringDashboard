from datetime import datetime, timezone

import mysql.connector
from mysql.connector.connection import MySQLConnection

from .config import get_settings


def get_connection() -> MySQLConnection:
    settings = get_settings()
    return mysql.connector.connect(
        host=settings.db_host,
        port=settings.db_port,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
    )


def ensure_schema() -> None:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS services (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                service_key VARCHAR(100) NOT NULL UNIQUE,
                host_name VARCHAR(255) NOT NULL,
                environment VARCHAR(50) NOT NULL,
                last_seen_at DATETIME NOT NULL,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                service_id BIGINT NOT NULL,
                ts DATETIME(3) NOT NULL,
                cpu_percent DECIMAL(5,2) NOT NULL,
                memory_percent DECIMAL(5,2) NOT NULL,
                disk_percent DECIMAL(5,2) NOT NULL,
                uptime_seconds BIGINT NOT NULL,
                FOREIGN KEY (service_id) REFERENCES services(id),
                INDEX idx_metrics_service_ts (service_id, ts)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                service_id BIGINT NOT NULL,
                ts DATETIME(3) NOT NULL,
                level VARCHAR(16) NOT NULL,
                message TEXT NOT NULL,
                FOREIGN KEY (service_id) REFERENCES services(id),
                INDEX idx_logs_service_ts (service_id, ts)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS anomalies (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                service_id BIGINT NOT NULL,
                metric_name VARCHAR(50) NOT NULL,
                ts DATETIME(3) NOT NULL,
                method VARCHAR(50) NOT NULL,
                score DECIMAL(10,4) NOT NULL,
                severity ENUM('low','medium','high','critical') NOT NULL,
                details_json JSON,
                FOREIGN KEY (service_id) REFERENCES services(id),
                INDEX idx_anomalies_service_ts (service_id, ts)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                service_id BIGINT NOT NULL,
                source_type ENUM('metric','log','prediction') NOT NULL,
                source_ref_id BIGINT,
                status ENUM('open','acknowledged','resolved','suppressed') NOT NULL DEFAULT 'open',
                severity ENUM('low','medium','high','critical') NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                dedup_key VARCHAR(255),
                cooldown_until DATETIME(3),
                opened_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                acknowledged_at DATETIME NULL,
                resolved_at DATETIME NULL,
                FOREIGN KEY (service_id) REFERENCES services(id),
                INDEX idx_alerts_service_status (service_id, status),
                INDEX idx_alerts_dedup (dedup_key)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_events (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                alert_id BIGINT NOT NULL,
                event_type ENUM('created','deduped','suppressed','acknowledged','resolved','reopened') NOT NULL,
                actor_type ENUM('system','user') NOT NULL,
                actor_id BIGINT NULL,
                event_ts DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                details_json JSON,
                FOREIGN KEY (alert_id) REFERENCES alerts(id),
                INDEX idx_alert_events_alert_ts (alert_id, event_ts)
            )
            """
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def now_utc_naive() -> datetime:
    # MySQL DATETIME stores naive values, so we normalize UTC without tzinfo.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def is_database_available() -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        finally:
            cursor.close()
            conn.close()
    except Exception:
        return False

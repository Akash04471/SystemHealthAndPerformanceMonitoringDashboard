from math import sqrt

from ..core.config import get_settings
from ..core.db import get_connection, now_utc_naive


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _stddev(values: list[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return sqrt(variance)


def _severity_from_zscore(zscore: float) -> str:
    abs_z = abs(zscore)
    if abs_z >= 4.0:
        return "critical"
    if abs_z >= 3.0:
        return "high"
    if abs_z >= 2.5:
        return "medium"
    return "low"


def run_zscore_detection(service_id: int, service_key: str) -> dict:
    settings = get_settings()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT ts, cpu_percent, memory_percent, disk_percent
            FROM metrics
            WHERE service_id = %s
            ORDER BY ts DESC
            LIMIT %s
            """,
            (service_id, settings.zscore_window_size),
        )
        rows = cursor.fetchall()

        if len(rows) < settings.zscore_min_points:
            if not rows:
                return {"anomalies_created": 0, "alerts_created": 0, "reason": "insufficient_points"}

            latest = rows[0]
            anomalies_created = 0
            alerts_created = 0

            for metric_name in ("cpu_percent", "memory_percent", "disk_percent"):
                latest_value = float(latest[metric_name])
                if latest_value < 95.0:
                    continue

                severity = "critical" if latest_value >= 99.0 else "high"
                event_time = now_utc_naive()
                cursor.execute(
                    """
                    INSERT INTO anomalies (service_id, metric_name, ts, method, score, severity, details_json)
                    VALUES (%s, %s, %s, %s, %s, %s, JSON_OBJECT('threshold', %s, 'value', %s, 'reason', 'insufficient_baseline'))
                    """,
                    (
                        service_id,
                        metric_name,
                        latest["ts"],
                        "bootstrap_threshold",
                        latest_value,
                        severity,
                        95.0,
                        latest_value,
                    ),
                )
                anomaly_id = cursor.lastrowid
                anomalies_created += 1

                dedup_key = f"{service_key}:{metric_name}:bootstrap-threshold"
                cursor.execute(
                    """
                    SELECT id FROM alerts
                    WHERE dedup_key = %s
                      AND status IN ('open', 'acknowledged')
                      AND (cooldown_until IS NULL OR cooldown_until > %s)
                    ORDER BY opened_at DESC
                    LIMIT 1
                    """,
                    (dedup_key, event_time),
                )
                open_alert = cursor.fetchone()

                if open_alert:
                    cursor.execute(
                        """
                        INSERT INTO alert_events (alert_id, event_type, actor_type, event_ts, details_json)
                        VALUES (%s, 'deduped', 'system', %s, JSON_OBJECT('anomaly_id', %s, 'value', %s))
                        """,
                        (open_alert["id"], event_time, anomaly_id, latest_value),
                    )
                    continue

                cursor.execute(
                    """
                    INSERT INTO alerts (
                        service_id, source_type, source_ref_id, status, severity,
                        title, description, dedup_key, opened_at, cooldown_until
                    )
                    VALUES (
                        %s, 'metric', %s, 'open', %s,
                        %s, %s, %s, %s, DATE_ADD(%s, INTERVAL %s MINUTE)
                    )
                    """,
                    (
                        service_id,
                        anomaly_id,
                        severity,
                        f"High {metric_name} without baseline",
                        f"Value {latest_value:.2f} exceeded bootstrap threshold 95 with insufficient baseline points",
                        dedup_key,
                        event_time,
                        event_time,
                        settings.alert_cooldown_minutes,
                    ),
                )
                alert_id = cursor.lastrowid
                alerts_created += 1

                cursor.execute(
                    """
                    INSERT INTO alert_events (alert_id, event_type, actor_type, event_ts, details_json)
                    VALUES (%s, 'created', 'system', %s, JSON_OBJECT('anomaly_id', %s, 'value', %s))
                    """,
                    (alert_id, event_time, anomaly_id, latest_value),
                )

            conn.commit()
            if anomalies_created or alerts_created:
                return {
                    "anomalies_created": anomalies_created,
                    "alerts_created": alerts_created,
                    "reason": "bootstrap_rule",
                }
            return {"anomalies_created": 0, "alerts_created": 0, "reason": "insufficient_points"}

        rows.reverse()
        latest = rows[-1]

        anomalies_created = 0
        alerts_created = 0

        for metric_name in ("cpu_percent", "memory_percent", "disk_percent"):
            series = [float(row[metric_name]) for row in rows]
            series_mean = _mean(series)
            series_std = _stddev(series, series_mean)
            if series_std == 0:
                continue

            latest_value = float(latest[metric_name])
            zscore = (latest_value - series_mean) / series_std
            if abs(zscore) < settings.zscore_threshold:
                continue

            severity = _severity_from_zscore(zscore)
            event_time = now_utc_naive()
            cursor.execute(
                """
                INSERT INTO anomalies (service_id, metric_name, ts, method, score, severity, details_json)
                VALUES (%s, %s, %s, %s, %s, %s, JSON_OBJECT('mean', %s, 'stddev', %s, 'value', %s))
                """,
                (
                    service_id,
                    metric_name,
                    latest["ts"],
                    "zscore",
                    zscore,
                    severity,
                    series_mean,
                    series_std,
                    latest_value,
                ),
            )
            anomaly_id = cursor.lastrowid
            anomalies_created += 1

            dedup_key = f"{service_key}:{metric_name}:zscore"
            cursor.execute(
                """
                SELECT id FROM alerts
                WHERE dedup_key = %s
                  AND status IN ('open', 'acknowledged')
                  AND (cooldown_until IS NULL OR cooldown_until > %s)
                ORDER BY opened_at DESC
                LIMIT 1
                """,
                (dedup_key, event_time),
            )
            open_alert = cursor.fetchone()

            if open_alert:
                cursor.execute(
                    """
                    INSERT INTO alert_events (alert_id, event_type, actor_type, event_ts, details_json)
                    VALUES (%s, 'deduped', 'system', %s, JSON_OBJECT('anomaly_id', %s, 'zscore', %s))
                    """,
                    (open_alert["id"], event_time, anomaly_id, zscore),
                )
                continue

            cursor.execute(
                """
                INSERT INTO alerts (
                    service_id, source_type, source_ref_id, status, severity,
                    title, description, dedup_key, opened_at, cooldown_until
                )
                VALUES (
                    %s, 'metric', %s, 'open', %s,
                    %s, %s, %s, %s, DATE_ADD(%s, INTERVAL %s MINUTE)
                )
                """,
                (
                    service_id,
                    anomaly_id,
                    severity,
                    f"Anomaly detected in {metric_name}",
                    f"Z-score {zscore:.2f} exceeded threshold {settings.zscore_threshold}",
                    dedup_key,
                    event_time,
                    event_time,
                    settings.alert_cooldown_minutes,
                ),
            )
            alert_id = cursor.lastrowid
            alerts_created += 1

            cursor.execute(
                """
                INSERT INTO alert_events (alert_id, event_type, actor_type, event_ts, details_json)
                VALUES (%s, 'created', 'system', %s, JSON_OBJECT('anomaly_id', %s, 'zscore', %s))
                """,
                (alert_id, event_time, anomaly_id, zscore),
            )

        conn.commit()
        return {
            "anomalies_created": anomalies_created,
            "alerts_created": alerts_created,
        }
    finally:
        cursor.close()
        conn.close()

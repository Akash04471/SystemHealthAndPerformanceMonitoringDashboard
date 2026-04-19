import time
import pandas as pd
import os
import mysql.connector
import matplotlib.pyplot as plt

REFRESH_SECONDS = 5
WINDOW_SIZE = 50


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

while True:
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=_require_env("DB_USER"),
        password=_require_env("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "system_monitoring"),
        port=int(os.getenv("DB_PORT", "3306")),
    )

    df = pd.read_sql(
        f"SELECT * FROM system_metrics ORDER BY timestamp DESC LIMIT {WINDOW_SIZE}",
        conn
    )
    conn.close()

    df = df.sort_values("timestamp")
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    plt.clf()
    plt.figure(figsize=(12, 6))

    plt.plot(df["timestamp"], df["cpu_percent"], label="CPU (%)")
    plt.plot(df["timestamp"], df["memory_percent"], label="Memory (%)")
    plt.plot(df["timestamp"], df["disk_percent"], label="Disk (%)")

    plt.axhline(80, linestyle="--", label="CPU Alert (80%)")
    plt.axhline(85, linestyle="--", label="Memory Alert (85%)")
    plt.axhline(70, linestyle="--", label="Disk Alert (70%)")

    plt.title("Real-Time System Health Monitoring")
    plt.xlabel("Time")
    plt.ylabel("Usage (%)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.pause(0.01)

    time.sleep(REFRESH_SECONDS)

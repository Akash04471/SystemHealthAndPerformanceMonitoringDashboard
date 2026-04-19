import pandas as pd
import os
import mysql.connector
import matplotlib.pyplot as plt


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    user=_require_env("DB_USER"),
    password=_require_env("DB_PASSWORD"),
    database=os.getenv("DB_NAME", "system_monitoring"),
    port=int(os.getenv("DB_PORT", "3306")),
)

df = pd.read_sql("SELECT * FROM system_metrics", conn)
conn.close()

df["timestamp"] = pd.to_datetime(df["timestamp"])

cpu_alerts = df[df["cpu_percent"] > 80]
memory_alerts = df[df["memory_percent"] > 85]
disk_alerts = df[df["disk_percent"] > 70]

print("ALERT SUMMARY")
print("----------------------------")
print(f"CPU alerts (>80%): {len(cpu_alerts)}")
print(f"Memory alerts (>85%): {len(memory_alerts)}")
print(f"Disk alerts (>70%): {len(disk_alerts)}")

plt.figure(figsize=(12, 6))

plt.plot(df["timestamp"], df["cpu_percent"], label="CPU Usage (%)")
plt.plot(df["timestamp"], df["memory_percent"], label="Memory Usage (%)")
plt.plot(df["timestamp"], df["disk_percent"], label="Disk Usage (%)")

plt.axhline(y=80, linestyle="--", linewidth=1.5, label="CPU Alert Threshold (80%)")
plt.axhline(y=85, linestyle="--", linewidth=1.5, label="Memory Alert Threshold (85%)")
plt.axhline(y=70, linestyle="--", linewidth=1.5, label="Disk Alert Threshold (70%)")

plt.title("System Resource Usage & Alerts Over Time")
plt.xlabel("Time")
plt.ylabel("Usage (%)")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()

plt.savefig("system_resource_usage_with_alerts.png")
plt.show()

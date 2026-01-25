import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="Akash@2004",
    database="system_monitoring",
    port=3306
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

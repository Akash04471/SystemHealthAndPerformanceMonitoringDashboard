import pandas as pd
import os
import mysql.connector


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

# --- MySQL connection ---
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    user=_require_env("DB_USER"),
    password=_require_env("DB_PASSWORD"),
    database=os.getenv("DB_NAME", "system_monitoring"),
    port=int(os.getenv("DB_PORT", "3306")),
)

# --- Load data ---
df = pd.read_sql("SELECT * FROM system_metrics", conn)
conn.close()

# --- KPI calculations ---
kpis = {
    "Average CPU Usage (%)": round(df["cpu_percent"].mean(), 2),
    "Maximum CPU Usage (%)": round(df["cpu_percent"].max(), 2),
    "Average Memory Usage (%)": round(df["memory_percent"].mean(), 2),
    "Maximum Disk Usage (%)": round(df["disk_percent"].max(), 2),
    "System Uptime (Hours)": round(df["uptime_seconds"].max() / 3600, 2),
    "Total Records Collected": len(df)
}

kpi_df = pd.DataFrame(list(kpis.items()), columns=["Metric", "Value"])

# --- Alerts ---
cpu_alerts = df[df["cpu_percent"] > 80]
memory_alerts = df[df["memory_percent"] > 85]

alerts_df = pd.concat([
    cpu_alerts.assign(Alert_Type="High CPU Usage"),
    memory_alerts.assign(Alert_Type="High Memory Usage")
])

# --- Write to Excel ---
with pd.ExcelWriter("system_health_dashboard.xlsx", engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Raw Metrics", index=False)
    kpi_df.to_excel(writer, sheet_name="KPI Summary", index=False)
    alerts_df.to_excel(writer, sheet_name="Alerts", index=False)

print("Excel dashboard file created successfully.")

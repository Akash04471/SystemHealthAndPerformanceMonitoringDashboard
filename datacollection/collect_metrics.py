import psutil
import datetime
import os
import mysql.connector


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

cursor = conn.cursor()

data = (
    datetime.datetime.now(),
    psutil.cpu_percent(interval=1),
    psutil.virtual_memory().percent,
    psutil.disk_usage('/').percent,
    int(datetime.datetime.now().timestamp() - psutil.boot_time())
)

cursor.execute("""
    INSERT INTO system_metrics 
    (timestamp, cpu_percent, memory_percent, disk_percent, uptime_seconds)
    VALUES (%s, %s, %s, %s, %s)
""", data)

conn.commit()
cursor.close()
conn.close()

print("Metrics inserted into MySQL:", data)

import psutil
import datetime
import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",          # change if different
    password="Akash@2004",
    database="system_monitoring",
    port=3306             # default MySQL port
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

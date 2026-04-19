import pandas as pd
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

query = "SELECT * FROM system_metrics"
df = pd.read_sql(query, conn)

conn.close()

print(df.head())

import pandas as pd
import mysql.connector

conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="Akash@2004",
    database="system_monitoring",
    port=3306
)

query = "SELECT * FROM system_metrics"
df = pd.read_sql(query, conn)

conn.close()

print(df.head())

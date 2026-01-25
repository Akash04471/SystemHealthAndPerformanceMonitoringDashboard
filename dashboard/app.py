import pandas as pd
import mysql.connector
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="System Health Dashboard", layout="wide")
st.title("🖥️ System Health & Performance Monitoring")

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

st.sidebar.header("Filters")
records = st.sidebar.slider("Number of recent records", 10, 500, 100)
df = df.tail(records)

col1, col2, col3 = st.columns(3)
col1.metric("Avg CPU (%)", round(df["cpu_percent"].mean(), 2))
col2.metric("Avg Memory (%)", round(df["memory_percent"].mean(), 2))
col3.metric("Avg Disk (%)", round(df["disk_percent"].mean(), 2))

fig = px.line(
    df,
    x="timestamp",
    y=["cpu_percent", "memory_percent", "disk_percent"],
    labels={"value": "Usage (%)", "timestamp": "Time"},
    title="System Resource Usage Over Time"
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("🚨 Alerts")
st.write("CPU > 80%", df[df["cpu_percent"] > 80].shape[0])
st.write("Memory > 85%", df[df["memory_percent"] > 85].shape[0])
st.write("Disk > 70%", df[df["disk_percent"] > 70].shape[0])

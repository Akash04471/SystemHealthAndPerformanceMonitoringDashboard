**System Health & Performance Monitoring**
Ever wondered what’s actually happening under the hood of your server? System Health & Performance Monitoring is a full-stack monitoring solution that transforms raw hardware telemetry into actionable insights. It doesn’t just watch your system—it remembers, analyzes, and visualizes its health in real-time.

**🚀 Why this exists**
-Most monitoring tools are either too simple or overly enterprise-heavy. This project bridges the gap by providing:
-Deep Memory: Persistent MySQL storage ensures you don't lose data when the script stops.
-Smart KPIs: Automatically flags performance bottlenecks (like RAM spikes or disk fatigue).
-Double-Threat Visuals: Offers both lightweight Matplotlib exports for reports and a sleek, interactive Streamlit app for real-time tracking.

**🛠️ The Engine Room (Tech Stack)**

-Python: The glue holding the logic, metric collection, and automation together.
-MySQL: Our source of truth for historical performance data.
-Pandas: For the heavy lifting—cleaning data and calculating operational trends.
-Streamlit & Matplotlib: The "face" of the project, turning rows of data into intuitive graphs.

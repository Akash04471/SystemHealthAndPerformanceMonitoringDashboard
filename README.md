# 🛡️ Cronacore | The Core of System Observability

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/React-18.0+-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/Docker-Enabled-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/MySQL-9.0+-4479A1?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL" />
</div>

---

**Cronacore** is a production-hardened observability platform designed for real-time telemetry ingestion, anomaly detection, and predictive forecasting. It features a professional **"Deep Enterprise Tech"** aesthetic, shimmering interactive branding, and a resilient distributed architecture.

## 🏗️ System Architecture

```mermaid
graph TD
    A[Remote Agents] -->|JSON Telemetry| B[FastAPI Ingestion]
    B -->|Structured Logs| C[(MySQL Cluster)]
    D[Cronacore Dashboard] -->|REST API| B
    E[Service Watchdog] -->|Heartbeat Check| C
    E -->|Alert Trigger| F[Alert Engine]
    G[Predictive Engine] -->|Linear Regression| D
```

## ✨ Key Features
- **Exquisite Real-Time Dashboard**: High-contrast, emerald-on-slate design with shimmering branding, custom sleek scrollbars, and staggered entry animations.
- **AI-Powered Forecasting**: Predictive analytics that forecast resource exhaustion (CPU/Disk/Memory) using linear regression models.
- **Automated Anomaly Detection**: Real-time detection of performance spikes and system deviations with visualized score chips.
- **Distributed Agent Monitoring**: Built-in **Service Watchdog** tracks agent heartbeats and flags offline or unstable services instantly.
- **High-Fidelity Visuals**: Advanced Recharts implementation with gradient area surfaces and custom "Glass-Dark" tooltips.
- **Docker-First Infrastructure**: Fully containerized stack for seamless, repeatable deployment across any environment.

## 🚀 Quick Start (Production Mode)

Ensure you have **Docker** installed, then run:

```bash
# Clone the repository
git clone https://github.com/Akash04471/SystemHealthAndPerformanceMonitoringDashboard.git

# Enter the project
cd SystemHealthAndPerformanceMonitoringDashboard

# Launch the full stack
docker-compose up --build -d
```

Access the dashboard at **`http://localhost:8080`**
- **Default User**: `admin@example.com`
- **Default Pass**: `admin123`

## 🛠️ Tech Stack
- **Backend**: Python 3.9+, FastAPI, SQLAlchemy, MySQL
- **Frontend**: React 18, Recharts, Vanilla CSS (Token-based)
- **Monitoring**: Custom Watchdog Service, Heartbeat Ingestion API
- **Deployment**: Docker, Docker Compose, Nginx Proxy

---

<div align="center">
  <p>Built with ❤️ by <b>Akash</b></p>
</div>

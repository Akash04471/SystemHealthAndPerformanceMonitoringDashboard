# Deployment Guide

This guide explains how to deploy the System Health Monitoring Dashboard to a production server (VPS) using Docker Compose.

## 1. Prerequisites
- A Linux server (Ubuntu 22.04+ recommended).
- Docker and Docker Compose installed.
- A domain name (optional but recommended for SSL).

## 2. Server Setup
Clone the repository on your server:
```bash
git clone https://github.com/Akash04471/SystemHealthAndPerformanceMonitoringDashboard.git
cd SystemHealthAndPerformanceMonitoringDashboard
```

Create a production `.env` file:
```bash
cp .env.example .env
nano .env
```
Update the following:
- `JWT_SECRET`: Generate a random long string.
- `DB_PASSWORD`: Set a strong password.
- `CORS_ORIGINS`: Set to your server's domain/IP.

## 3. Launching with Docker
Build and start the services in detached mode:
```bash
docker-compose up -d --build
```

The dashboard will be available at `http://YOUR_SERVER_IP:8080`.

## 4. Enabling SSL (HTTPS)
We recommend using **Nginx Proxy Manager** or **Certbot** with a standalone Nginx container.

To use Certbot on the host:
1. Install Certbot: `sudo apt install certbot`.
2. Map port 80 and 443 to the host.
3. Update `frontend/nginx.conf` to include the SSL certificate paths.

## 5. Security Checklist
- [ ] Change all default passwords.
- [ ] Close port 3306 (MySQL) in your cloud provider's firewall (only allow local Docker access).
- [ ] Ensure `APP_ENV` is set to `production` in `.env`.
- [ ] Regularly update Docker images: `docker-compose pull && docker-compose up -d`.

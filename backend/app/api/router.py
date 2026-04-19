from fastapi import APIRouter

from .routes import alerts, anomalies, auth, dashboard, health, ingestion, metrics

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(ingestion.router, prefix="/ingest", tags=["ingestion"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["read"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["analytics"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])

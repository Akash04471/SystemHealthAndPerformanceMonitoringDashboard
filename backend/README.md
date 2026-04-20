# Backend Phase 2

This folder contains the Phase 2 FastAPI backend implementation.

## Run Locally

1. Create and activate a virtual environment.
2. Install dependencies from repository root:
  pip install -r backend/requirements.txt
3. Ensure environment variables are set in repository root .env file.
4. Start API from repository root:
  python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

## Run Tests

1. Install test dependencies from repository root:
  pip install -r backend/requirements-dev.txt
2. Run backend tests from repository root:
  pytest backend/tests -q

## Available Endpoints

- Health
  - GET /api/v1/health/live
  - GET /api/v1/health/ready
- Auth
  - POST /api/v1/auth/login
  - POST /api/v1/auth/refresh
  - POST /api/v1/auth/logout
  - GET /api/v1/auth/me
- Ingestion
  - POST /api/v1/ingest/metrics
  - POST /api/v1/ingest/logs
  - POST /api/v1/ingest/services/register
- Read
  - GET /api/v1/metrics
- Analytics
  - GET /api/v1/anomalies
- Alerts
  - GET /api/v1/alerts
  - POST /api/v1/alerts/{alert_id}/ack
  - POST /api/v1/alerts/{alert_id}/resolve
  - GET /api/v1/alerts/{alert_id}/events

## Notes

- JWT access and refresh tokens are implemented.
- Login endpoint includes basic per-client rate limiting (`LOGIN_RATE_LIMIT_WINDOW_SECONDS`, `LOGIN_RATE_LIMIT_MAX_ATTEMPTS`).
- API responses include `X-Request-ID` and structured request logs for traceability.
- Non-development environments can enforce strict CORS (`STRICT_CORS_IN_NON_DEV=true`) to block local origins.
- Service registration, metric ingestion, and log ingestion persist to MySQL tables.
- Z-score anomaly detection runs after metrics ingestion.
- Alerts and alert events are generated with deduplication and cooldown handling.

## Bootstrap Login

Use these credentials from environment variables:
- `BOOTSTRAP_ADMIN_EMAIL`
- `BOOTSTRAP_ADMIN_PASSWORD`

The login response returns bearer tokens for protected endpoints.

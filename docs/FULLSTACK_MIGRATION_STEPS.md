# AI-Based Real-Time System Monitoring and Predictive Analytics

## Goal
Convert the current Python + Streamlit prototype into a production-style full-stack application with:
- agent-based data collection
- API-first backend
- scalable database schema
- AI analytics (anomaly + prediction + log intelligence)
- real-time dashboard (React + WebSocket)
- secure deployment and CI/CD

## Current Baseline in This Repository
- Data collector writes directly to MySQL
- Dashboard reads directly from MySQL
- Analytics scripts are local Python scripts

This plan migrates incrementally so your current app keeps working while new components are added.

## Phase 0: Project Setup and Branching
1. Create a feature branch for migration work.
2. Add a top-level project layout:
   - backend/
   - frontend/
   - collector_agent/
   - worker/
   - infra/
   - docs/
3. Add environment files:
   - .env.example
   - backend/.env.example
   - frontend/.env.example
4. Move all hardcoded credentials to environment variables immediately.

Deliverable:
- Secure config baseline with no secrets hardcoded in source files.

## Phase 1: Define and Apply Target Architecture
Architecture flow:
Collector agents -> ingestion API -> database -> AI analytics service -> WebSocket layer -> React dashboard -> background workers -> notifications

Implementation steps:
1. Keep MySQL as primary transactional store.
2. Build a backend API service (FastAPI recommended).
3. Add Redis for:
   - queue broker for background workers
   - pub/sub for real-time WebSocket fanout
4. Add worker service (Celery recommended) for asynchronous analytics and alert processing.
5. Add notification adapters (email, Slack, webhook) behind a provider interface.

Deliverable:
- Architecture decision record in docs with selected stack and responsibilities.

## Phase 2: Redesign Database Schema
Create dedicated tables:
1. users
2. services
3. metrics
4. logs
5. anomalies
6. predictions
7. alerts
8. alert_events
9. audit_logs

Implementation steps:
1. Add migration tooling (Alembic recommended).
2. Create initial migration for new schema.
3. Add core indexes:
   - metrics(service_id, ts)
   - logs(service_id, ts)
   - anomalies(service_id, ts)
   - predictions(service_id, prediction_ts)
   - alerts(service_id, status)
4. Add dedup and cooldown support columns in alerts.
5. Keep old table (system_metrics) during transition.

Deliverable:
- Versioned schema migration applied locally and in CI.

## Phase 3: Backend APIs in Required Sequence
### 3A. Auth APIs first
Endpoints:
- POST /auth/login
- POST /auth/refresh
- POST /auth/logout
- GET /auth/me

Tasks:
1. Add JWT access token and refresh token support.
2. Add password hashing.
3. Add role claims (admin, operator, viewer).

### 3B. Ingestion APIs second
Endpoints:
- POST /ingest/metrics
- POST /ingest/logs
- POST /services/register

Tasks:
1. Require service identity and token.
2. Validate payload schema.
3. Return per-item ingest status.

### 3C. Read APIs third
Endpoints:
- GET /metrics
- GET /logs
- GET /anomalies
- GET /predictions
- GET /services

Tasks:
1. Add filtering by service and time range.
2. Add pagination for logs and alerts.

### 3D. Alert lifecycle APIs fourth
Endpoints:
- GET /alerts
- POST /alerts/{id}/ack
- POST /alerts/{id}/resolve
- POST /alerts/{id}/suppress
- GET /alerts/{id}/events

### 3E. Dashboard summary APIs fifth
Endpoints:
- GET /dashboard/summary
- GET /dashboard/kpi
- GET /dashboard/live-feed

Deliverable:
- End-to-end API path from ingestion to visible dashboard summary.

## Phase 4: Upgrade Collector to Agent Model
Implement in collector_agent:
1. collect()
2. serialize_payload()
3. send_to_api() with retry and timeout

Required reliability behavior:
1. Add service identity metadata:
   - service_key
   - host_name
   - environment
2. Add auth token header.
3. Add retries with exponential backoff and jitter.
4. Add local buffering when API is down:
   - write failed payloads to queue file
   - replay queue when API is healthy
5. Add idempotency key per payload batch.

Deliverable:
- Agent can survive temporary API/network failures without data loss.

## Phase 5: Smart Alerting Implementation
### Phase A: Statistical anomaly detection
1. Compute rolling mean and rolling standard deviation.
2. Compute z-score for each metric point.
3. Trigger anomaly when absolute z-score crosses threshold for N consecutive points.

### Phase B: ML anomaly detection
1. Train Isolation Forest per metric or per service profile.
2. Save anomaly score and decision label.
3. Write results to anomalies table.

### Phase C: Noise reduction
1. Deduplicate alerts using dedup_key.
2. Add suppression windows for known maintenance periods.
3. Add cooldown before reopening same condition.

Deliverable:
- High signal alerts with reduced duplicate noise.

## Phase 6: Predictive Monitoring
1. Build feature pipeline from historical metrics:
   - rolling averages
   - trend slopes
   - volatility
   - anomaly frequency
2. Train failure-risk model (start with Logistic Regression or Gradient Boosting).
3. Store:
   - risk_score
   - risk_window_start
   - risk_window_end
   - explanation_json (top contributing features)
4. Expose predictions in API and stream updates in real time.

Deliverable:
- Failure risk forecast available on dashboard per service.

## Phase 7: Log Intelligence
Step-up roadmap:
1. Baseline keyword classification (error, timeout, oom, disk full).
2. TF-IDF + Logistic Regression for incident category classification.
3. Optional incident summarization for clustered high-volume logs.
4. Correlate logs with anomaly windows and open alerts.

Deliverable:
- Logs become actionable intelligence, not just raw text.

## Phase 8: Build React Role-Based Dashboard
Create pages:
1. Login
2. Overview
3. Service Details
4. Alerts
5. Log Intelligence
6. Predictions
7. Admin

UI capabilities:
1. KPI cards and status chips.
2. Global time filter and service filter.
3. Annotated time-series charts.
4. Live event feed panel.
5. Role-based navigation and route guards.

Deliverable:
- Full-stack UI with clear RBAC behavior and real-time observability.

## Phase 9: Real-Time Streaming
1. WebSocket as primary channel.
2. Polling fallback endpoint for degraded mode.
3. Stream event types:
   - metric points
   - anomalies
   - alert events
   - prediction updates
4. Add client auto-reconnect with backoff.

Deliverable:
- Production-like live monitoring experience.

## Phase 10: Security Hardening
1. JWT access + refresh rotation.
2. RBAC authorization middleware on all protected routes.
3. Rate limiting on auth and ingest endpoints.
4. Environment-based secrets only.
5. Audit logging for critical actions.
6. Input schema validation and payload size limits.
7. CORS policy with explicit origins.

Deliverable:
- Security posture suitable for interview demos and real deployments.

## Phase 11: DevOps and Deployment
1. Dockerize services:
   - backend
   - worker
   - frontend
   - collector agent
2. Add docker-compose for local integrated run.
3. CI/CD pipeline stages:
   - lint
   - test
   - build image
   - deploy
4. Add readiness and health endpoints for all services.
5. Add monitoring and logs for deployed stack.

Deliverable:
- Reproducible deployments with automated validation.

## Suggested Execution Timeline
### Week 1
- Phase 0, 1, 2
- Auth and ingestion APIs from Phase 3

### Week 2
- Read APIs, dashboard summary APIs, collector agent migration

### Week 3
- Smart alerting (Phase A to C), alert lifecycle APIs, React pages (Overview + Alerts)

### Week 4
- Predictive monitoring, log intelligence, full realtime streaming, security hardening, CI/CD

## Definition of Done Checklist
1. Collectors no longer write directly to DB.
2. Dashboard no longer reads DB directly; it uses APIs.
3. WebSocket live feed works with polling fallback.
4. Alert lifecycle (open, ack, resolve, suppress) is complete and audited.
5. Predictions include risk score and explainability payload.
6. RBAC enforced across backend and frontend routes.
7. Secrets are environment-managed and not in source code.
8. Docker compose can run the whole stack locally.
9. CI pipeline runs lint, tests, and build successfully.

## Immediate Next Task List (Start Here)
1. Create backend service skeleton and migration setup.
2. Implement Auth APIs and token model.
3. Implement Ingestion APIs with validation and service identity.
4. Refactor collector to send_to_api() with retries and local queue.
5. Add first dashboard summary endpoint and connect frontend prototype.

# Next Remaining Steps

## Current Status
Phase 3 is functionally complete and merged to main.

## Progress Update (2026-04-20)
- Backend automated test baseline is added and passing (`6 passed`).
- Added backend test files and tooling setup (`pytest` + `httpx`) for local CI-ready execution.
- Frontend automated test baseline is added and passing (`3 passed`).
- Added Vitest + React Testing Library setup for Phase 3 UI flows.
- Added GitHub Actions CI workflow to run backend tests and frontend tests/build on push and pull requests.

## Priority 1: Automated Testing
- Extend backend tests beyond auth/health to include dashboard, alerts, and anomalies endpoints.
- Extend frontend tests beyond baseline scenarios to include resolve action, manual refresh, and auto-refresh timer behavior.
- Add integration tests that run frontend + backend together.

## Priority 2: CI/CD Quality Gates
- Extend CI with backend lint/static checks in addition to tests.
- Extend CI with frontend lint/static checks in addition to tests/build.
- Block merges if required checks fail.

## Priority 3: Security Hardening
- Move secrets to environment or secret manager for non-local environments.
- Restrict CORS to exact production origins only.
- Add auth failure logging and basic rate limiting for login endpoints.

## Priority 4: Deployment Readiness
- Define deployment targets for backend and frontend.
- Create environment-specific configuration for dev, staging, and production.
- Add a release checklist with rollback steps.

## Priority 5: Observability and Reliability
- Add structured backend logs and request IDs.
- Add frontend and backend error monitoring.
- Add health checks and uptime alerting.

## Suggested Execution Order
1. Testing baseline (backend + frontend)
2. CI checks
3. Security hardening
4. Staging deployment
5. Production rollout

## Definition of Done for Next Phase
- Automated tests run in CI and pass.
- Staging environment is deployed and validated.
- Security and observability baselines are in place.
- Production deployment plan is documented and tested.

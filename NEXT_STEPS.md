# Next Remaining Steps

## Current Status
Phase 4 hardening baseline is complete and merged locally for validation.

## Progress Update (2026-04-20)
- Backend tests expanded and passing (`10 passed`) including dashboard, alerts, and anomalies endpoint coverage.
- Frontend tests expanded and passing (`6 passed`) including resolve action and refresh behavior.
- CI expanded with static checks (backend compile, frontend build) in addition to tests.
- Security hardening added: login rate limiting and auth failure logging.
- Observability baseline added: `X-Request-ID` response header and structured request logging.
- Environment hardening added: strict non-dev CORS enforcement controls and documented env vars.

## Priority 1: Automated Testing
- Add integration tests that run frontend + backend together.

## Priority 2: CI/CD Quality Gates
- Block merges if required checks fail.

## Priority 3: Security Hardening
- Move secrets to environment or secret manager for non-local environments.
- Restrict CORS to exact production origins only.

## Priority 4: Deployment Readiness
- Define deployment targets for backend and frontend.
- Create environment-specific configuration for dev, staging, and production.
- Add a release checklist with rollback steps.

## Priority 5: Observability and Reliability
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

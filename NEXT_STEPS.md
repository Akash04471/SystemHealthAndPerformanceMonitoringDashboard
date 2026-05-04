# Next Remaining Steps

## Current Status
Phase 3 is functionally complete and merged to main.

## Progress Update (2026-04-20)
- Backend automated test baseline is added and passing (`6 passed`).
- Added backend test files and tooling setup (`pytest` + `httpx`) for local CI-ready execution.
- Frontend automated test baseline is added and passing (`3 passed`).
- Added Vitest + React Testing Library setup for Phase 3 UI flows.
- Added GitHub Actions CI workflow to run backend tests and frontend tests/build on push and pull requests.
- Added Phase 4 collector agent implementation with buffered backend ingestion and retry support.

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

## Strict Frontend Test Matrix (Phase 4 UI)

### Happy Path
1. Login with valid credentials and confirm dashboard loads summary, alerts, and anomalies.
2. Acknowledge an open alert and verify status changes in list and counters.
3. Resolve an open alert and verify status changes in list and counters.
4. Apply status, severity, and service filters and verify visible list updates correctly.
5. Click `Refresh now` and confirm data and `Last update` timestamp refresh.
6. Keep auto-refresh enabled for at least two cycles and confirm periodic updates.

### Failure Path
1. Use invalid login credentials and verify friendly login error is shown.
2. Trigger access-token expiry scenario and verify UI shows session-expired behavior with recovery via re-login.
3. Trigger repeated failed login attempts and verify 429-friendly message appears.
4. Stop backend during active session and verify friendly failure state appears (without app crash).
5. Restart backend and verify dashboard can recover via manual refresh or reload.

### Edge Cases
1. Confirm `X-Request-ID` visibility appears in UI when API errors occur.
2. Verify alert action buttons disable correctly for `acknowledged` and `resolved` states.
3. Set refresh seconds to boundary values (5 and 120) and verify polling still works.
4. Toggle auto-refresh off and verify `Last update` no longer changes automatically.
5. Toggle auto-refresh back on and verify polling resumes.
6. Validate behavior when lists are empty (no layout break, no console errors).

### Exit Criteria Before Push
1. Frontend tests pass: `npm run test:run`.
2. Frontend production build passes: `npm run build`.
3. No blocking browser console errors during manual validation.
4. All Happy Path, Failure Path, and Edge Case checks are completed.

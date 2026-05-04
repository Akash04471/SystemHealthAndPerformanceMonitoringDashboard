# Collector Agent

This module implements the Phase 4 collector agent model for the monitoring system.

## Features

- Collects system metrics with service identity metadata
- Serializes payloads for backend ingestion API
- Sends data to the backend with bearer token authentication
- Retries failed sends with exponential backoff and jitter
- Buffers failed payloads locally to `collector_agent/queue.jsonl`
- Replays buffered payloads on next agent run
- Adds an idempotency key per payload batch via `Idempotency-Key`

## Usage

1. Install dependencies:
   ```bash
   python -m pip install -r collector_agent/requirements.txt
   ```

2. Set environment variables in `.env` or your shell. Example values:
   ```env
   COLLECTOR_API_URL=http://127.0.0.1:8000/api/v1
   COLLECTOR_SERVICE_KEY=collector-agent
   COLLECTOR_HOST_NAME=collector-host
   COLLECTOR_ENVIRONMENT=development
   COLLECTOR_AUTH_EMAIL=admin@example.com
   COLLECTOR_AUTH_PASSWORD=admin123
   COLLECTOR_QUEUE_FILE=collector_agent/queue.jsonl
   ```

3. Run the collector:
   ```bash
   python collector_agent/app.py
   ```

## Notes

- If `COLLECTOR_ACCESS_TOKEN` is provided, the agent will use it directly.
- If authentication fails, the agent will retry and queue payloads locally.
- The queue file is ignored by default in `.gitignore`.

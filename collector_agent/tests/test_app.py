import json
from pathlib import Path

import pytest

from collector_agent import app as collector_app


def test_queue_payload_writes_and_reads_queue(tmp_path, monkeypatch):
    queue_file = tmp_path / "queue.jsonl"
    monkeypatch.setattr(collector_app, "QUEUE_FILE", queue_file)

    payload = {"identity": {"service_key": "collector-agent"}, "points": []}
    collector_app.queue_payload(payload, "idempotency-key-123")

    assert queue_file.exists()
    entries = collector_app._read_queue()
    assert len(entries) == 1
    assert entries[0]["idempotency_key"] == "idempotency-key-123"
    assert entries[0]["payload"] == payload


def test_replay_queue_success_removes_queued_payload(tmp_path, monkeypatch):
    queue_file = tmp_path / "queue.jsonl"
    monkeypatch.setattr(collector_app, "QUEUE_FILE", queue_file)

    payload = {"identity": {"service_key": "collector-agent"}, "points": []}
    collector_app.queue_payload(payload, "idempotency-key-123")

    monkeypatch.setattr(collector_app, "send_with_retry", lambda payload, idempotency_key: {"status": "accepted"})
    collector_app.replay_queue()

    assert not queue_file.exists()


def test_replay_queue_keeps_retryable_payload(tmp_path, monkeypatch):
    queue_file = tmp_path / "queue.jsonl"
    monkeypatch.setattr(collector_app, "QUEUE_FILE", queue_file)

    payload = {"identity": {"service_key": "collector-agent"}, "points": []}
    collector_app.queue_payload(payload, "idempotency-key-123")

    def failing_send(payload, idempotency_key):
        raise collector_app.RetryableError("Temporary failure")

    monkeypatch.setattr(collector_app, "send_with_retry", failing_send)
    collector_app.replay_queue()

    assert queue_file.exists()
    entries = collector_app._read_queue()
    assert len(entries) == 1
    assert entries[0]["idempotency_key"] == "idempotency-key-123"


def test_replay_queue_drops_non_retryable_payload(tmp_path, monkeypatch):
    queue_file = tmp_path / "queue.jsonl"
    monkeypatch.setattr(collector_app, "QUEUE_FILE", queue_file)

    payload = {"identity": {"service_key": "collector-agent"}, "points": []}
    collector_app.queue_payload(payload, "idempotency-key-123")

    def fatal_send(payload, idempotency_key):
        raise collector_app.AgentError("Fatal error")

    monkeypatch.setattr(collector_app, "send_with_retry", fatal_send)
    collector_app.replay_queue()

    assert not queue_file.exists()

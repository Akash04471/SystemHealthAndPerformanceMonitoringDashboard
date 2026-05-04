import json
import logging
import os
import random
import shutil
import socket
import time
import uuid
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
# Load .env from collector_agent dir or root dir
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR.parent / ".env")

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None

QUEUE_FILE = Path(os.getenv("COLLECTOR_QUEUE_FILE", BASE_DIR / "queue.jsonl"))
API_URL = os.getenv("COLLECTOR_API_URL", "http://127.0.0.1:8000/api/v1")
SERVICE_KEY = os.getenv("COLLECTOR_SERVICE_KEY", "collector-agent")
HOST_NAME = os.getenv("COLLECTOR_HOST_NAME", socket.gethostname())
ENVIRONMENT = os.getenv("COLLECTOR_ENVIRONMENT", "development")
ACCESS_TOKEN = os.getenv("COLLECTOR_ACCESS_TOKEN")
AUTH_EMAIL = os.getenv("COLLECTOR_AUTH_EMAIL") or os.getenv("BOOTSTRAP_ADMIN_EMAIL")
AUTH_PASSWORD = os.getenv("COLLECTOR_AUTH_PASSWORD") or os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
MAX_RETRIES = int(os.getenv("COLLECTOR_RETRY_MAX", "5"))
BACKOFF_BASE = float(os.getenv("COLLECTOR_RETRY_BACKOFF_BASE", "1.0"))
BACKOFF_CAP = float(os.getenv("COLLECTOR_RETRY_BACKOFF_CAP", "30.0"))
TIMEOUT_SECONDS = float(os.getenv("COLLECTOR_TIMEOUT_SECONDS", "10"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("collector_agent")


class AgentError(Exception):
    pass


class AuthError(AgentError):
    pass


class RetryableError(AgentError):
    pass


def _json_headers(token: str, idempotency_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idempotency_key,
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json_bytes(body: bytes) -> dict[str, object]:
    return json.loads(body.decode("utf-8"))


def _collect_metrics_point() -> dict[str, object]:
    if psutil:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage("/").percent
        uptime_seconds = int(time.time() - psutil.boot_time())
    else:
        cpu_percent = 0.0
        memory_percent = 0.0
        root_path = Path.cwd().anchor
        disk_usage = shutil.disk_usage(root_path)
        disk_percent = round(disk_usage.used / disk_usage.total * 100.0, 1) if disk_usage.total else 0.0
        uptime_seconds = 0

    return {
        "timestamp": _now_iso(),
        "cpu_percent": round(cpu_percent, 2),
        "memory_percent": round(memory_percent, 2),
        "disk_percent": round(disk_percent, 2),
        "uptime_seconds": uptime_seconds,
    }


def collect() -> dict[str, object]:
    return _collect_metrics_point()


def serialize_payload(point: dict[str, object]) -> dict[str, object]:
    return {
        "identity": {
            "service_key": SERVICE_KEY,
            "host_name": HOST_NAME,
            "environment": ENVIRONMENT,
        },
        "points": [point],
    }


def get_access_token() -> str:
    if ACCESS_TOKEN:
        return ACCESS_TOKEN

    if not AUTH_EMAIL or not AUTH_PASSWORD:
        raise AuthError("Collector auth credentials are not configured")

    login_url = f"{API_URL}/auth/login"
    request_body = json.dumps({"email": AUTH_EMAIL, "password": AUTH_PASSWORD}).encode("utf-8")
    request = urllib.request.Request(
        login_url,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            payload = _load_json_bytes(response.read())
            token = str(payload.get("access_token", ""))
            if not token:
                raise AuthError("Failed to obtain access token from auth/login")
            return token
    except urllib.error.HTTPError as exc:
        raise AuthError(f"Authentication failed: {exc.code} {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise RetryableError(f"Auth endpoint unreachable: {exc}") from exc


def _send_api_request(payload: dict[str, object], token: str, idempotency_key: str) -> dict[str, object]:
    url = f"{API_URL}/ingest/metrics"
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=_json_headers(token, idempotency_key), method="POST")

    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            if 200 <= response.status < 300:
                return _load_json_bytes(response.read())
            raise RetryableError(f"Unexpected response status: {response.status}")
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            raise AuthError("Unauthorized access token") from exc
        if exc.code in {429} or 500 <= exc.code < 600:
            raise RetryableError(f"Retryable HTTP error {exc.code}") from exc
        payload_text = exc.read().decode("utf-8", errors="ignore")
        raise AgentError(f"API rejected request: {exc.code} {payload_text}") from exc
    except urllib.error.URLError as exc:
        raise RetryableError(f"Network error: {exc}") from exc


def send_to_api(payload: dict[str, object], token: str, idempotency_key: str) -> dict[str, object]:
    return _send_api_request(payload, token, idempotency_key)


def _backoff_delay(attempt: int) -> float:
    raw = BACKOFF_BASE * (2 ** (attempt - 1))
    return min(BACKOFF_CAP, raw + random.uniform(0, 1))


def send_with_retry(payload: dict[str, object], idempotency_key: str) -> dict[str, object]:
    last_error: Exception | None = None
    token = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            token = get_access_token()
            return send_to_api(payload, token, idempotency_key)
        except AuthError as exc:
            last_error = exc
            if ACCESS_TOKEN:
                raise
            logger.warning("Auth failed; retrying login on next attempt")
        except RetryableError as exc:
            last_error = exc
            delay = _backoff_delay(attempt)
            logger.warning("Retryable error: %s; retrying in %.1fs", exc, delay)
            time.sleep(delay)
            continue
        except AgentError as exc:
            raise
    raise last_error or AgentError("Unknown failure sending payload")


def queue_payload(payload: dict[str, object], idempotency_key: str) -> None:
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "payload": payload,
        "idempotency_key": idempotency_key,
        "queued_at": _now_iso(),
    }
    with QUEUE_FILE.open("a", encoding="utf-8") as queue_fd:
        queue_fd.write(json.dumps(entry) + "\n")
    logger.info("Queued payload for later retry: %s", QUEUE_FILE)


def _read_queue() -> list[dict[str, object]]:
    if not QUEUE_FILE.exists():
        return []

    entries: list[dict[str, object]] = []
    with QUEUE_FILE.open("r", encoding="utf-8") as queue_fd:
        for line in queue_fd:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                logger.warning("Skipping invalid queued payload line")
    return entries


def _write_queue(entries: list[dict[str, object]]) -> None:
    if not entries:
        try:
            QUEUE_FILE.unlink()
        except FileNotFoundError:
            pass
        return

    with QUEUE_FILE.open("w", encoding="utf-8") as queue_fd:
        for entry in entries:
            queue_fd.write(json.dumps(entry) + "\n")


def replay_queue() -> None:
    entries = _read_queue()
    if not entries:
        return

    logger.info("Replaying %d queued payload(s)", len(entries))
    remaining: list[dict[str, object]] = []

    for entry in entries:
        payload = entry.get("payload")
        key = entry.get("idempotency_key")
        if not payload or not key:
            continue

        try:
            send_with_retry(payload, key)
            logger.info("Replayed queued payload successfully: %s", key)
        except RetryableError:
            remaining.append(entry)
        except Exception as exc:
            logger.warning("Dropping queued payload due to non-retryable error: %s", exc)

    _write_queue(remaining)


def generate_idempotency_key() -> str:
    return str(uuid.uuid4())


def run() -> None:
    logger.info("Starting collector agent against %s", API_URL)
    try:
        replay_queue()
    except Exception as exc:
        logger.warning("Unable to replay queued payloads: %s", exc)

    point = collect()
    payload = serialize_payload(point)
    key = generate_idempotency_key()

    try:
        response = send_with_retry(payload, key)
        logger.info("Payload sent successfully: %s", response)
    except RetryableError as exc:
        logger.warning("Send failed after retries; queueing payload: %s", exc)
        queue_payload(payload, key)
    except Exception as exc:
        logger.error("Collector failed: %s", exc)
        queue_payload(payload, key)


if __name__ == "__main__":
    run()

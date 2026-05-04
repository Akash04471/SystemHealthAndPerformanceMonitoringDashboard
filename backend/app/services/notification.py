import json
import logging
import urllib.request
from datetime import datetime

from ..core.config import get_settings

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def notify_alert(alert_id: int, title: str, severity: str, service_key: str, description: str):
        settings = get_settings()
        if not settings.notification_enabled:
            return

        message = (
            f"🚨 *New Alert Created*\n"
            f"*ID:* {alert_id}\n"
            f"*Severity:* {severity.upper()}\n"
            f"*Service:* {service_key}\n"
            f"*Title:* {title}\n"
            f"*Description:* {description}\n"
            f"*Time:* {datetime.now().isoformat()}"
        )

        # Always log to console
        logger.info("Notification: %s", message)

        if settings.notification_webhook:
            NotificationService._send_webhook(settings.notification_webhook, message)

    @staticmethod
    def _send_webhook(url: str, message: str):
        payload = {"text": message}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as f:
                res = f.read()
                logger.info("Webhook sent successfully: %s", res.decode("utf-8"))
        except Exception as e:
            logger.error("Failed to send webhook: %s", str(e))

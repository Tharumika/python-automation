from __future__ import annotations

from datetime import UTC, datetime

import httpx


class NotificationConnector:
    def __init__(self, timeout_seconds: int = 10) -> None:
        self.timeout_seconds = timeout_seconds

    def send(
        self,
        target: str,
        subject: str,
        message: str,
        dry_run: bool,
        webhook_url: str | None = None,
    ) -> dict:
        payload = {
            "target": target,
            "subject": subject,
            "message": message,
            "processed_at": datetime.now(UTC).isoformat(),
        }
        return self._deliver(payload=payload, webhook_url=webhook_url, dry_run=dry_run)

    def create_incident(
        self,
        queue: str,
        title: str,
        description: str,
        dry_run: bool,
        webhook_url: str | None = None,
    ) -> dict:
        payload = {
            "queue": queue,
            "title": title,
            "description": description,
            "processed_at": datetime.now(UTC).isoformat(),
        }
        return self._deliver(payload=payload, webhook_url=webhook_url, dry_run=dry_run)

    def _deliver(self, payload: dict, webhook_url: str | None, dry_run: bool) -> dict:
        if dry_run:
            return {
                "delivery": "simulated",
                "webhook_configured": bool(webhook_url),
                **payload,
            }

        if not webhook_url:
            return {
                "delivery": "recorded_local",
                "webhook_configured": False,
                "note": "No outbound webhook URL configured, so the action was recorded only.",
                **payload,
            }

        response = httpx.post(webhook_url, json=payload, timeout=self.timeout_seconds)
        response.raise_for_status()

        return {
            "delivery": "completed",
            "webhook_configured": True,
            "webhook_status_code": response.status_code,
            **payload,
        }

from __future__ import annotations

from datetime import UTC, datetime


class NotificationConnector:
    def send(self, target: str, subject: str, message: str, dry_run: bool) -> dict:
        delivery = "simulated" if dry_run else "recorded"
        return {
            "delivery": delivery,
            "target": target,
            "subject": subject,
            "message": message,
            "processed_at": datetime.now(UTC).isoformat(),
        }

    def create_incident(self, queue: str, title: str, description: str, dry_run: bool) -> dict:
        delivery = "simulated" if dry_run else "recorded"
        return {
            "delivery": delivery,
            "queue": queue,
            "title": title,
            "description": description,
            "processed_at": datetime.now(UTC).isoformat(),
        }

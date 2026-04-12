from __future__ import annotations

from datetime import UTC, datetime

import httpx


class NotificationConnector:
    def __init__(self, timeout_seconds: int = 10) -> None:
        self.timeout_seconds = timeout_seconds

    def send_notification(
        self,
        target: str,
        subject: str,
        message: str,
        dry_run: bool,
        slack_webhook_url: str | None = None,
        notification_webhook_url: str | None = None,
        slack_destination_label: str = "platform-ops",
    ) -> dict:
        destination_label = target or slack_destination_label
        payload = {
            "destination_label": destination_label,
            "subject": subject,
            "message": message,
            "processed_at": datetime.now(UTC).isoformat(),
        }

        if slack_webhook_url:
            slack_payload = self._build_slack_payload(
                destination_label=destination_label,
                subject=subject,
                message=message,
            )
            return self._deliver(
                payload=payload,
                request_payload=slack_payload,
                webhook_url=slack_webhook_url,
                dry_run=dry_run,
                connector_type="slack_webhook",
                destination_label=destination_label,
            )

        if notification_webhook_url:
            generic_payload = {
                "text": f"{subject}\n{message}",
                "subject": subject,
                "message": message,
                "destination_label": destination_label,
                "test_traffic": "[TEST]" in subject or "test" in message.lower(),
            }
            return self._deliver(
                payload=payload,
                request_payload=generic_payload,
                webhook_url=notification_webhook_url,
                dry_run=dry_run,
                connector_type="generic_webhook",
                destination_label=destination_label,
            )

        return self._record_only(
            payload=payload,
            connector_type="record_only",
            destination_label=destination_label,
        )

    def create_incident(
        self,
        queue: str,
        title: str,
        description: str,
        dry_run: bool,
        webhook_url: str | None = None,
    ) -> dict:
        destination_label = queue
        payload = {
            "destination_label": destination_label,
            "title": title,
            "description": description,
            "processed_at": datetime.now(UTC).isoformat(),
        }
        request_payload = {
            "title": title,
            "description": description,
            "destination_label": destination_label,
            "test_traffic": "[TEST]" in title or "test" in description.lower(),
        }
        if webhook_url:
            return self._deliver(
                payload=payload,
                request_payload=request_payload,
                webhook_url=webhook_url,
                dry_run=dry_run,
                connector_type="incident_webhook",
                destination_label=destination_label,
            )
        return self._record_only(
            payload=payload,
            connector_type="record_only",
            destination_label=destination_label,
        )

    def _deliver(
        self,
        payload: dict,
        request_payload: dict,
        webhook_url: str,
        dry_run: bool,
        connector_type: str,
        destination_label: str,
    ) -> dict:
        if dry_run:
            return {
                "connector_type": connector_type,
                "delivery": "simulated",
                "destination_label": destination_label,
                "webhook_configured": True,
                "request_preview": request_payload,
                **payload,
            }

        response = httpx.post(webhook_url, json=request_payload, timeout=self.timeout_seconds)
        response.raise_for_status()

        return {
            "connector_type": connector_type,
            "delivery": "completed",
            "destination_label": destination_label,
            "webhook_configured": True,
            "webhook_status_code": response.status_code,
            **payload,
        }

    def _record_only(self, payload: dict, connector_type: str, destination_label: str) -> dict:
        return {
            "connector_type": connector_type,
            "delivery": "recorded_local",
            "destination_label": destination_label,
            "webhook_configured": False,
            "note": "No outbound webhook URL configured, so the action was recorded only.",
            **payload,
        }

    def _build_slack_payload(self, destination_label: str, subject: str, message: str) -> dict:
        return {
            "text": f"{subject} -> {message}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": subject[:150],
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Destination*\n{destination_label}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Connector*\nSlack Incoming Webhook",
                        },
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message[:2800],
                    },
                },
            ],
        }

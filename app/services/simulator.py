from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


SCENARIOS = ("monitoring", "audit", "pubsub")


def build_simulated_event(scenario: str, project_id: str) -> tuple[dict[str, str], dict[str, Any]]:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unsupported simulator scenario '{scenario}'.")

    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    event_id = f"sim-{scenario}-{uuid4().hex[:12]}"

    if scenario == "monitoring":
        headers = {
            "ce-id": event_id,
            "ce-type": "google.cloud.monitoring.alert.v1.opened",
            "ce-source": f"//monitoring.googleapis.com/projects/{project_id}/alerts/demo-monitoring",
            "ce-time": timestamp,
        }
        payload = {
            "data": {
                "incident": {
                    "state": "open",
                    "summary": "Simulated high CPU usage detected on a production VM",
                },
                "resource": {
                    "type": "gce_instance",
                    "labels": {
                        "project_id": project_id,
                        "instance_id": "vm-demo-01",
                        "location": "us-central1-a",
                    },
                    "name": f"projects/{project_id}/zones/us-central1-a/instances/vm-demo-01",
                },
            }
        }
        return headers, payload

    if scenario == "audit":
        headers = {
            "ce-id": event_id,
            "ce-type": "google.cloud.audit.log.v1.written",
            "ce-source": f"//cloudaudit.googleapis.com/projects/{project_id}/logs/activity",
            "ce-time": timestamp,
        }
        payload = {
            "data": {
                "resourceName": f"projects/{project_id}",
                "resource": {
                    "type": "project",
                    "labels": {
                        "project_id": project_id,
                        "location": "global",
                    },
                },
                "protoPayload": {
                    "serviceName": "cloudresourcemanager.googleapis.com",
                    "methodName": "SetIamPolicy",
                    "resourceName": f"projects/{project_id}",
                    "authenticationInfo": {
                        "principalEmail": "security.admin@example.com",
                    },
                },
            }
        }
        return headers, payload

    headers = {
        "content-type": "application/json",
    }
    payload = {
        "subscription": f"projects/{project_id}/subscriptions/demo-subscription",
        "message": {
            "messageId": event_id,
            "publishTime": timestamp,
            "attributes": {
                "region": "asia-south1",
                "deliveryAttempt": "4",
            },
            "data": "eyJldmVudCI6ICJkZWFkbGV0dGVyIiwgIm1lc3NhZ2UiOiAiU3Vic2NyaWJlciByZXRyaWVzIGFyZSByaXNpbmcifQ==",
        },
    }
    return headers, payload

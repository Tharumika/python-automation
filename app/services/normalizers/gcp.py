from __future__ import annotations

import base64
import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from app.schemas.events import NormalizedEventCandidate


def peek_identity(headers: dict[str, str], payload: dict[str, Any]) -> tuple[str, str]:
    normalized_headers = {key.lower(): value for key, value in headers.items()}
    source = normalized_headers.get("ce-source")
    event_type = normalized_headers.get("ce-type")

    if source and event_type:
        return source, event_type

    if "subscription" in payload and "message" in payload:
        return payload.get("subscription", "pubsub"), "google.cloud.pubsub.push"

    return payload.get("source", "google.cloud.unknown"), payload.get(
        "type", "google.cloud.unknown"
    )


def normalize_gcp_event(
    headers: dict[str, str],
    payload: dict[str, Any],
    default_project_id: str,
) -> NormalizedEventCandidate:
    normalized_headers = {key.lower(): value for key, value in headers.items()}

    if "ce-type" in normalized_headers:
        return _normalize_cloudevent(normalized_headers, payload, default_project_id)

    if "subscription" in payload and "message" in payload:
        return _normalize_pubsub_push(payload, default_project_id)

    return _normalize_generic(payload, default_project_id)


def _normalize_cloudevent(
    headers: dict[str, str],
    payload: dict[str, Any],
    default_project_id: str,
) -> NormalizedEventCandidate:
    data = payload.get("data", payload)
    resource = data.get("resource", {}) if isinstance(data, dict) else {}
    resource_labels = resource.get("labels", {}) if isinstance(resource, dict) else {}
    incident = data.get("incident", {}) if isinstance(data, dict) else {}
    proto_payload = data.get("protoPayload", {}) if isinstance(data, dict) else {}

    source = headers["ce-source"]
    event_type = headers["ce-type"]
    occurred_at = _parse_timestamp(headers.get("ce-time") or payload.get("time"))
    project_id = (
        resource_labels.get("project_id")
        or data.get("project")
        or data.get("projectId")
        or default_project_id
    )
    region = (
        resource_labels.get("location")
        or data.get("resourceLocation", {}).get("currentLocations", [None])[0]
    )
    resource_id = (
        data.get("resourceName")
        or resource.get("name")
        or payload.get("subject")
        or incident.get("resource_name")
    )
    resource_type = resource.get("type") or incident.get("resource_type")
    metadata_json = {
        "cloud_event_id": headers.get("ce-id"),
        "cloud_event_subject": headers.get("ce-subject"),
        "service_name": proto_payload.get("serviceName"),
        "method_name": proto_payload.get("methodName"),
        "principal_email": (
            proto_payload.get("authenticationInfo", {}).get("principalEmail")
            if isinstance(proto_payload.get("authenticationInfo"), dict)
            else None
        ),
        "incident_state": incident.get("state"),
        "incident_summary": incident.get("summary"),
        "resource_labels": resource_labels,
    }
    severity = _infer_severity(event_type, data, metadata_json)

    return NormalizedEventCandidate(
        source=source,
        event_type=event_type,
        severity=severity,
        project_id=str(project_id),
        region=region,
        resource_id=resource_id,
        resource_type=resource_type,
        occurred_at=occurred_at,
        dedupe_key=_build_dedupe_key(
            headers.get("ce-id"),
            headers.get("ce-source"),
            headers.get("ce-type"),
            resource_id,
            occurred_at.isoformat(),
        ),
        metadata_json=metadata_json,
    )


def _normalize_pubsub_push(
    payload: dict[str, Any],
    default_project_id: str,
) -> NormalizedEventCandidate:
    message = payload.get("message", {})
    attributes = message.get("attributes", {})
    decoded_payload = _decode_pubsub_data(message.get("data"))
    subscription = payload.get("subscription", "projects/demo/subscriptions/unknown")
    project_id = _extract_project_id(subscription) or default_project_id
    message_id = message.get("messageId")
    occurred_at = _parse_timestamp(message.get("publishTime"))
    metadata_json = {
        "subscription": subscription,
        "attributes": attributes,
        "decoded_payload": decoded_payload,
    }
    severity = _infer_severity("google.cloud.pubsub.push", decoded_payload, metadata_json)

    return NormalizedEventCandidate(
        source=subscription,
        event_type="google.cloud.pubsub.push",
        severity=severity,
        project_id=project_id,
        region=attributes.get("region"),
        resource_id=message_id,
        resource_type="pubsub_message",
        occurred_at=occurred_at,
        dedupe_key=_build_dedupe_key(message_id, subscription, "google.cloud.pubsub.push"),
        metadata_json=metadata_json,
    )


def _normalize_generic(
    payload: dict[str, Any],
    default_project_id: str,
) -> NormalizedEventCandidate:
    occurred_at = _parse_timestamp(payload.get("time") or payload.get("timestamp"))
    source = payload.get("source", "google.cloud.generic")
    event_type = payload.get("type", "google.cloud.generic")
    resource_id = payload.get("resourceId") or payload.get("resource_id")
    severity = _infer_severity(event_type, payload, payload)

    return NormalizedEventCandidate(
        source=source,
        event_type=event_type,
        severity=severity,
        project_id=payload.get("projectId", default_project_id),
        region=payload.get("region"),
        resource_id=resource_id,
        resource_type=payload.get("resourceType"),
        occurred_at=occurred_at,
        dedupe_key=_build_dedupe_key(source, event_type, resource_id, occurred_at.isoformat()),
        metadata_json=payload,
    )


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC)

    if not value:
        return datetime.now(UTC)

    normalized = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).astimezone(UTC)
    except ValueError:
        return datetime.now(UTC)


def _extract_project_id(subscription: str) -> str | None:
    parts = subscription.split("/")
    if len(parts) >= 2 and parts[0] == "projects":
        return parts[1]
    return None


def _decode_pubsub_data(encoded_data: str | None) -> dict[str, Any]:
    if not encoded_data:
        return {}

    try:
        decoded = base64.b64decode(encoded_data).decode("utf-8")
    except Exception:
        return {"raw_data": encoded_data}

    try:
        return json.loads(decoded)
    except json.JSONDecodeError:
        return {"message": decoded}


def _build_dedupe_key(*parts: Any) -> str:
    material = "|".join(str(part) for part in parts if part)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _infer_severity(
    event_type: str,
    payload: dict[str, Any],
    metadata_json: dict[str, Any],
) -> str:
    lowered_type = event_type.lower()
    serialized_payload = json.dumps(payload, sort_keys=True, default=str).lower()

    if "monitoring" in lowered_type or payload.get("incident"):
        incident_state = str(metadata_json.get("incident_state", "")).lower()
        if incident_state == "open":
            return "critical"
        return "high"

    if "audit" in lowered_type:
        risky_methods = ("setiampolicy", "delete", "disable", "update", "remove")
        method_name = str(metadata_json.get("method_name", "")).lower()
        if any(marker in method_name for marker in risky_methods):
            return "high"
        return "medium"

    if "pubsub" in lowered_type:
        if "deadletter" in serialized_payload or "deliveryattempt" in serialized_payload:
            return "high"
        return "medium"

    if "error" in serialized_payload or "failed" in serialized_payload:
        return "high"

    return "info"

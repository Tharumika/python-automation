from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Rule


DEFAULT_RULES = [
    {
        "name": "Notify on GCP monitoring incidents",
        "description": "Opens an operations notification workflow for Eventarc monitoring alerts.",
        "source_filter": "*monitoring*",
        "event_type_filter": "google.cloud.monitoring.alert.*",
        "severity_filter": "high,critical",
        "action_type": "notify",
        "action_target": "platform-ops",
        "priority": 10,
    },
    {
        "name": "Escalate IAM or destructive audit changes",
        "description": "Creates an incident when high-risk audit log changes are detected.",
        "source_filter": "*cloudaudit*",
        "event_type_filter": "google.cloud.audit.log.v1.written",
        "severity_filter": "high,critical",
        "action_type": "create_incident",
        "action_target": "security-response",
        "priority": 20,
    },
    {
        "name": "Track Pub/Sub delivery pressure",
        "description": "Notifies the platform team about queue delivery issues and subscriber retries.",
        "event_type_filter": "google.cloud.pubsub.push",
        "severity_filter": "medium,high,critical",
        "action_type": "notify",
        "action_target": "messaging-ops",
        "priority": 30,
    },
]


def seed_default_rules(db: Session) -> None:
    existing_names = {name for (name,) in db.query(Rule.name).all()}
    for payload in DEFAULT_RULES:
        if payload["name"] in existing_names:
            continue
        db.add(Rule(**payload))
    db.commit()

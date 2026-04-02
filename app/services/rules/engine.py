from __future__ import annotations

from fnmatch import fnmatch
from typing import Any

from sqlalchemy.orm import Session

from app.models import NormalizedEvent, Rule


def get_matching_rules(db: Session, event: NormalizedEvent, enabled: bool) -> list[Rule]:
    if not enabled:
        return []

    rules = (
        db.query(Rule)
        .filter(Rule.enabled.is_(True))
        .order_by(Rule.priority.asc(), Rule.created_at.asc())
        .all()
    )
    return [rule for rule in rules if _matches_rule(rule, event)]


def _matches_rule(rule: Rule, event: NormalizedEvent) -> bool:
    if not _matches_filter(rule.source_filter, event.source):
        return False
    if not _matches_filter(rule.event_type_filter, event.event_type):
        return False
    if not _matches_filter(rule.severity_filter, event.severity):
        return False
    if not _matches_filter(rule.resource_type_filter, event.resource_type):
        return False
    if not _matches_conditions(rule.conditions_json, event.metadata_json):
        return False
    return True


def _matches_filter(rule_filter: str | None, value: str | None) -> bool:
    if not rule_filter:
        return True
    if value is None:
        return False

    candidates = [item.strip().lower() for item in rule_filter.split(",") if item.strip()]
    lowered_value = value.lower()
    return any(fnmatch(lowered_value, candidate) for candidate in candidates)


def _matches_conditions(conditions: dict[str, Any], metadata_json: dict[str, Any]) -> bool:
    metadata_contains = conditions.get("metadata_contains", {})
    if not isinstance(metadata_contains, dict):
        return False

    for key, expected in metadata_contains.items():
        actual = metadata_json.get(key)
        if isinstance(expected, list):
            lowered_expected = {str(item).lower() for item in expected}
            if str(actual).lower() not in lowered_expected:
                return False
            continue
        if str(actual).lower() != str(expected).lower():
            return False

    return True

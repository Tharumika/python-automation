import json


def test_ingest_monitoring_event_creates_workflow_run(client, fixtures_dir):
    payload = json.loads((fixtures_dir / "gcp_monitoring_incident.json").read_text())
    headers = {
        "x-api-key": "test-key",
        "ce-id": "evt-monitoring-001",
        "ce-type": "google.cloud.monitoring.alert.v1.opened",
        "ce-source": "//monitoring.googleapis.com/projects/demo-project/alerts/alert-001",
        "ce-time": "2026-04-02T16:05:00Z",
    }

    response = client.post("/api/v1/events/ingest", json=payload, headers=headers)

    assert response.status_code == 202
    body = response.json()
    assert body["normalized_event"]["severity"] == "critical"
    assert body["matched_rule_names"] == ["Notify on GCP monitoring incidents"]
    assert len(body["workflow_runs"]) == 1
    assert body["workflow_runs"][0]["status"] == "simulated"
    assert body["workflow_runs"][0]["action_type"] == "notify"


def test_ingest_audit_event_creates_incident_workflow(client, fixtures_dir):
    payload = json.loads((fixtures_dir / "gcp_audit_log_event.json").read_text())
    headers = {
        "x-api-key": "test-key",
        "ce-id": "evt-audit-001",
        "ce-type": "google.cloud.audit.log.v1.written",
        "ce-source": "//cloudaudit.googleapis.com/projects/demo-project/logs/activity",
        "ce-time": "2026-04-02T16:10:00Z",
    }

    response = client.post("/api/v1/events/ingest", json=payload, headers=headers)

    assert response.status_code == 202
    body = response.json()
    assert body["normalized_event"]["severity"] == "high"
    assert body["matched_rule_names"] == ["Escalate IAM or destructive audit changes"]
    assert body["workflow_runs"][0]["action_type"] == "create_incident"


def test_duplicate_event_returns_conflict(client, fixtures_dir):
    payload = json.loads((fixtures_dir / "gcp_monitoring_incident.json").read_text())
    headers = {
        "x-api-key": "test-key",
        "ce-id": "evt-monitoring-dup",
        "ce-type": "google.cloud.monitoring.alert.v1.opened",
        "ce-source": "//monitoring.googleapis.com/projects/demo-project/alerts/alert-dup",
        "ce-time": "2026-04-02T16:20:00Z",
    }

    first = client.post("/api/v1/events/ingest", json=payload, headers=headers)
    second = client.post("/api/v1/events/ingest", json=payload, headers=headers)

    assert first.status_code == 202
    assert second.status_code == 409

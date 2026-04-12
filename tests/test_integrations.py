from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


class DummyResponse:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        return None


def build_client(**overrides) -> tuple[TestClient, Path]:
    runtime_dir = Path(__file__).parent / "runtime"
    runtime_dir.mkdir(exist_ok=True)
    database_path = runtime_dir / f"integrations-{uuid4().hex}.db"
    config = {
        "database_url": f"sqlite:///{database_path.as_posix()}",
        "allowed_ingest_api_keys": "test-key",
        "default_gcp_project_id": "demo-project",
        "dry_run": True,
    }
    config.update(overrides)
    settings = Settings(**config)
    app = create_app(settings)
    return TestClient(app), database_path


def cleanup_db(database_path: Path) -> None:
    for suffix in ("", "-shm", "-wal"):
        candidate = Path(f"{database_path}{suffix}")
        if candidate.exists():
            candidate.unlink()


def test_integration_status_endpoint(client):
    response = client.get("/api/v1/integrations/status")

    assert response.status_code == 200
    assert response.json() == {
        "mode": "dry-run",
        "dry_run": True,
        "slack_configured": False,
        "slack_destination_label": "platform-ops",
        "notification_webhook_configured": False,
        "incident_webhook_configured": False,
    }


def test_notify_integration_prefers_slack_over_generic_webhook(monkeypatch):
    calls = []

    def fake_post(url, json, timeout):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return DummyResponse(200)

    monkeypatch.setattr("app.services.connectors.notifications.httpx.post", fake_post)

    client, database_path = build_client(
        dry_run=False,
        slack_webhook_url="https://hooks.slack.test/services/abc",
        notification_webhook_url="https://notify.test/webhook",
    )

    with client:
        response = client.post("/api/v1/integrations/test/notify")
        assert response.status_code == 200
        body = response.json()
        assert body["connector_type"] == "slack_webhook"
        assert body["delivery"] == "completed"

    cleanup_db(database_path)

    assert len(calls) == 1
    assert calls[0]["url"] == "https://hooks.slack.test/services/abc"
    assert "blocks" in calls[0]["json"]


def test_notify_integration_falls_back_to_generic_webhook(monkeypatch):
    calls = []

    def fake_post(url, json, timeout):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return DummyResponse(200)

    monkeypatch.setattr("app.services.connectors.notifications.httpx.post", fake_post)

    client, database_path = build_client(
        dry_run=False,
        notification_webhook_url="https://notify.test/webhook",
    )

    with client:
        response = client.post("/api/v1/integrations/test/notify")
        assert response.status_code == 200
        body = response.json()
        assert body["connector_type"] == "generic_webhook"
        assert body["delivery"] == "completed"

    cleanup_db(database_path)

    assert len(calls) == 1
    assert calls[0]["url"] == "https://notify.test/webhook"
    assert calls[0]["json"]["destination_label"] == "integration-test"


def test_notify_integration_uses_record_only_without_webhooks():
    client, database_path = build_client(dry_run=False)

    with client:
        response = client.post("/api/v1/integrations/test/notify")
        assert response.status_code == 200
        body = response.json()
        assert body["connector_type"] == "record_only"
        assert body["delivery"] == "recorded_local"
        workflow_response = client.get(f"/api/v1/workflow-runs/{body['workflow_run_id']}")
        assert workflow_response.status_code == 200
        assert workflow_response.json()["result_payload"]["delivery"] == "recorded_local"

    cleanup_db(database_path)


def test_incident_integration_uses_incident_webhook(monkeypatch):
    calls = []

    def fake_post(url, json, timeout):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return DummyResponse(202)

    monkeypatch.setattr("app.services.connectors.notifications.httpx.post", fake_post)

    client, database_path = build_client(
        dry_run=False,
        incident_webhook_url="https://incident.test/webhook",
    )

    with client:
        response = client.post("/api/v1/integrations/test/incident")
        assert response.status_code == 200
        body = response.json()
        assert body["connector_type"] == "incident_webhook"
        assert body["delivery"] == "completed"

    cleanup_db(database_path)

    assert len(calls) == 1
    assert calls[0]["url"] == "https://incident.test/webhook"
    assert "[TEST]" in calls[0]["json"]["title"]

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_manual_queue_processing_flow():
    runtime_dir = Path(__file__).parent / "runtime"
    runtime_dir.mkdir(exist_ok=True)
    database_path = runtime_dir / f"queue-{uuid4().hex}.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path.as_posix()}",
        allowed_ingest_api_keys="test-key",
        default_gcp_project_id="demo-project",
        dry_run=True,
        auto_process_workflow_queue=False,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        ingest_response = client.post("/api/v1/simulator/events/monitoring")
        assert ingest_response.status_code == 202
        workflow_id = ingest_response.json()["workflow_runs"][0]["id"]
        assert ingest_response.json()["workflow_runs"][0]["status"] == "queued"

        summary_response = client.get("/dashboard/summary")
        assert summary_response.status_code == 200
        assert summary_response.json()["queue_depth"] == 1
        assert summary_response.json()["processing_mode"] == "manual queue processing"

        process_response = client.post("/api/v1/workflow-runs/process-queue?limit=10")
        assert process_response.status_code == 200
        assert process_response.json()["processed_count"] == 1
        assert workflow_id in process_response.json()["processed_workflow_run_ids"]

        workflow_response = client.get(f"/api/v1/workflow-runs/{workflow_id}")
        assert workflow_response.status_code == 200
        assert workflow_response.json()["status"] == "simulated"

    for suffix in ("", "-shm", "-wal"):
        candidate = Path(f"{database_path}{suffix}")
        if candidate.exists():
            candidate.unlink()

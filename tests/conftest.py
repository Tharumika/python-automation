from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    runtime_dir = Path(__file__).parent / "runtime"
    runtime_dir.mkdir(exist_ok=True)
    database_path = runtime_dir / f"test-{uuid4().hex}.db"
    settings = Settings(
        database_url=f"sqlite:///{database_path.as_posix()}",
        allowed_ingest_api_keys="test-key",
        default_gcp_project_id="demo-project",
        dry_run=True,
    )
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
    for suffix in ("", "-shm", "-wal"):
        candidate = Path(f"{database_path}{suffix}")
        if candidate.exists():
            candidate.unlink()


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"

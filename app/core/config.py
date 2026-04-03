from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GCP Cloud Ops Automation Hub"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./cloud_ops.db"
    allowed_ingest_api_keys: str = "dev-ingest-key"
    default_gcp_project_id: str = "demo-project"
    enable_rule_engine: bool = True
    dry_run: bool = True
    log_level: str = "INFO"
    webhook_timeout_seconds: int = 10
    notification_webhook_url: str | None = None
    incident_webhook_url: str | None = None
    auto_process_workflow_queue: bool = True
    workflow_queue_batch_size: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @computed_field  # type: ignore[misc]
    @property
    def ingest_api_keys(self) -> set[str]:
        return {
            key.strip()
            for key in self.allowed_ingest_api_keys.split(",")
            if key.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import events, health, rules, workflow_runs
from app.core.config import Settings, get_settings
from app.db.session import DatabaseManager
from app.services.rules.seed import seed_default_rules


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = active_settings
        app.state.db = DatabaseManager(active_settings.database_url)
        app.state.db.create_all()

        for db in app.state.db.session():
            seed_default_rules(db)

        try:
            yield
        finally:
            app.state.db.dispose()

    app = FastAPI(
        title=active_settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(health.router)
    app.include_router(events.router, prefix=active_settings.api_prefix)
    app.include_router(rules.router, prefix=active_settings.api_prefix)
    app.include_router(workflow_runs.router, prefix=active_settings.api_prefix)

    @app.get("/", tags=["root"])
    def read_root() -> dict[str, str]:
        return {
            "message": active_settings.app_name,
            "docs": "/docs",
        }

    return app


app = create_app()

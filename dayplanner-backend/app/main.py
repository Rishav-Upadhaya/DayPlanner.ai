from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import prepare_legacy_database_for_alembic, run_startup_schema_migrations
from app.core.rate_limit import RateLimitMiddleware
from app.models import *  # noqa: F401,F403
from app.workers.calendar_sync_worker import start_calendar_sync_worker, stop_calendar_sync_worker
from app.workers.engagement_worker import start_engagement_worker, stop_engagement_worker

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    alembic_cfg = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
    prepare_legacy_database_for_alembic(alembic_cfg)
    command.upgrade(alembic_cfg, 'head')
    run_startup_schema_migrations()
    start_calendar_sync_worker()
    start_engagement_worker()
    try:
        yield
    finally:
        stop_engagement_worker()
        stop_calendar_sync_worker()

app = FastAPI(
    title=settings.app_name,
    version='0.1.0',
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    lifespan=lifespan,
)
app.include_router(api_router, prefix=settings.api_v1_prefix)

app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_allow_origins.split(',') if origin.strip()],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/health', tags=['health'])
def health() -> dict[str, str]:
    return {'status': 'ok'}

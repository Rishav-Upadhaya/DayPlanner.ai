import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

TEST_DB_PATH = Path(__file__).resolve().parents[1] / 'test_dayplanner.db'
os.environ['DATABASE_URL'] = f'sqlite:///{TEST_DB_PATH}'
os.environ['ENABLE_BACKGROUND_SYNC'] = 'false'

from app.core.config import get_settings

get_settings.cache_clear()

from app.core.database import run_startup_schema_migrations

from app.main import app
from app.models import *  # noqa: F401,F403


settings = get_settings()
if settings.database_url.startswith('sqlite:///'):
    sqlite_path = settings.database_url.replace('sqlite:///', '', 1)
    db_file = Path(sqlite_path)
    if db_file.exists():
        db_file.unlink()


alembic_cfg = Config(str(Path(__file__).resolve().parents[1] / 'alembic.ini'))
command.upgrade(alembic_cfg, 'head')
run_startup_schema_migrations()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    email = f"test-{uuid4().hex[:12]}@example.com"
    signup_response = client.post(
        '/api/v1/auth/signup',
        json={
            'email': email,
            'full_name': 'Test User',
            'password': 'StrongPass123!',
        },
    )
    assert signup_response.status_code == 200
    payload = signup_response.json()
    access_token = payload['access_token']
    user_id = payload['user_id']
    return {
        'Authorization': f'Bearer {access_token}',
        'X-User-Id': user_id,
    }

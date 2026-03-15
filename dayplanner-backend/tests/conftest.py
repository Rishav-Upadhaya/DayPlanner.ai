from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine, run_startup_schema_migrations
from app.main import app
from app.models import *  # noqa: F401,F403


Base.metadata.create_all(bind=engine)
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

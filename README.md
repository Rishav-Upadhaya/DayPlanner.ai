# DayPlanner Workspace

Single-command local stack for frontend + backend + Postgres + Adminer.

## Run everything

From workspace root:

- `docker compose up --build`

## Services

- Frontend: `http://localhost:9002`
- Backend API: `http://localhost:8000`
- Backend OpenAPI: `http://localhost:8000/api/v1/openapi.json`
- Adminer: `http://localhost:8080`
- Postgres: `localhost:5432`

## Environment overrides

Optional host environment variables consumed by compose:

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `GOOGLE_OAUTH_CLIENT_ID`
- `GOOGLE_OAUTH_CLIENT_SECRET`
- `GOOGLE_OAUTH_REDIRECT_URI`
- `GOOGLE_CALENDAR_WEBHOOK_SECRET`
- `ENABLE_BACKGROUND_SYNC`
- `BACKGROUND_SYNC_INTERVAL_SECONDS`
- `ENABLE_BACKGROUND_SYNC_LEADER_LOCK`
- `BACKGROUND_SYNC_LEADER_LOCK_ID`

## Notes

- Backend now uses FastAPI lifespan hooks (startup/shutdown) for DB init and worker lifecycle.
- Calendar background sync supports Postgres advisory-lock leader election to avoid duplicate workers in multi-instance scenarios.

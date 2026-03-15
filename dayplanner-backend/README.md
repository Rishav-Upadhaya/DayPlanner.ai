# DayPlanner Backend

FastAPI + LangGraph + Postgres backend for DayPlanner AI.

## Quick Start

1. Create virtual env and install dependencies:
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
2. Copy env:
   - `cp .env.example .env`
3. Run API:
   - `uvicorn app.main:app --reload --port 8000`
4. Open docs:
   - `http://localhost:8000/api/v1/docs`

## Current Scope

- v1 routers for auth, plans, chat, calendar, history, settings, memory.
- LangGraph and GraphRAG service skeleton in place.
- Tracking docs to execute full production implementation.

from datetime import datetime, timezone
import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user_id
from app.core.config import get_settings
from app.core.database import get_db
from app.integrations.google_calendar import GoogleCalendarClient
from app.integrations.google_oauth import GoogleOAuthClient
from app.repositories.calendar import CalendarRepository
from app.repositories.users import UserRepository
from app.services.calendar_sync import CalendarSyncService
from app.services.oauth_state import create_oauth_state, verify_oauth_state
from app.schemas.calendar_actions import ConflictResolutionRequest
from app.schemas.calendar import CalendarAccountDTO, CalendarConflictDTO

router = APIRouter()
oauth_client = GoogleOAuthClient()
google_calendar_client = GoogleCalendarClient()
logger = logging.getLogger(__name__)


@router.get('/accounts', response_model=list[CalendarAccountDTO])
def list_accounts(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> list[CalendarAccountDTO]:
    repository = CalendarRepository(db)
    rows = repository.list_accounts(user_id=user_id)
    return [
        CalendarAccountDTO(
            id=row.id,
            provider=row.provider,
            email=row.email,
            status=row.status,
            last_synced_at=row.last_synced_at.isoformat() if row.last_synced_at else None,
        )
        for row in rows
    ]


@router.post('/accounts/google/start')
def connect_google(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> dict[str, str]:
    settings = get_settings()
    user_repository = UserRepository(db)
    if not settings.google_oauth_client_id:
        raise HTTPException(status_code=503, detail='Google OAuth is not configured: missing GOOGLE_OAUTH_CLIENT_ID')

    app_user = user_repository.get_by_id(user_id=user_id)
    if not app_user:
        raise HTTPException(status_code=404, detail='Logged-in user not found')

    redirect_uri = f"{settings.frontend_url.rstrip('/')}/auth/callback/google-calendar"
    state = create_oauth_state(purpose='calendar_connect', user_id=user_id)

    redirect_url = oauth_client.build_auth_url(
        client_id=settings.google_oauth_client_id,
        redirect_uri=redirect_uri,
        scope='https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/calendar.events.readonly',
        state=state,
        login_hint=app_user.email,
    )
    return {
        'redirect_url': redirect_url,
        'user_id': user_id,
        'scope': 'https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/calendar.events.readonly',
    }


@router.post('/accounts/google/callback')
def connect_google_callback(code: str, state: str, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> dict[str, str]:
    settings = get_settings()
    repository = CalendarRepository(db)
    user_repository = UserRepository(db)

    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
        raise HTTPException(status_code=503, detail='Google OAuth is not configured: missing GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_SECRET')

    try:
        verify_oauth_state(token=state, expected_purpose='calendar_connect', expected_user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail='Invalid OAuth state') from exc

    redirect_uri = f"{settings.frontend_url.rstrip('/')}/auth/callback/google-calendar"
    try:
        token_data = oauth_client.exchange_code(
            client_id=settings.google_oauth_client_id,
            client_secret=settings.google_oauth_client_secret,
            redirect_uri=redirect_uri,
            code=code,
        )
        app_user = user_repository.get_by_id(user_id=user_id)
        if not app_user:
            raise HTTPException(status_code=404, detail='Logged-in user not found')

        email = app_user.email.strip().lower()

        repository.upsert_google_token(
            user_id=user_id,
            email=email,
            access_token=token_data.get('access_token', ''),
            refresh_token=token_data.get('refresh_token', ''),
            scope=token_data.get('scope', ''),
            expires_in_seconds=token_data.get('expires_in', 3600),
            token_type=token_data.get('token_type', 'Bearer'),
        )
    except HTTPException:
        raise
    except Exception as exc:
        error_message = str(exc).strip() or 'unknown_error'
        logger.exception('Google calendar account linking failed for user_id=%s: %s', user_id, error_message)
        raise HTTPException(status_code=502, detail=f'Google calendar account linking failed: {error_message}') from exc

    return {'status': 'connected', 'provider': 'google', 'email': email}


@router.post('/sync-all')
def sync_all(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> dict[str, str]:
    today = datetime.now(timezone.utc).date().isoformat()
    service = CalendarSyncService(db=db, settings=get_settings(), calendar_client=google_calendar_client, oauth_client=oauth_client)
    result = service.sync_user_for_day(user_id=user_id, day=today)

    return {
        'status': str(result.get('status', 'synced')),
        'user_id': user_id,
        'accounts': str(result.get('accounts', 0)),
        'events_ingested': str(result.get('events_ingested', 0)),
        'conflicts_generated': str(result.get('conflicts_generated', 0)),
        'synced_at': datetime.now(timezone.utc).isoformat(),
    }


@router.get('/conflicts', response_model=list[CalendarConflictDTO])
def get_conflicts(date: str, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> list[CalendarConflictDTO]:
    repository = CalendarRepository(db)
    rows = repository.list_conflicts(user_id=user_id, day=date)
    return [CalendarConflictDTO(id=row.id, description=row.description, status=row.status) for row in rows]


@router.post('/conflicts/{conflict_id}/resolve', response_model=CalendarConflictDTO)
def resolve_conflict(
    conflict_id: str,
    payload: ConflictResolutionRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> CalendarConflictDTO:
    repository = CalendarRepository(db)
    resolved = repository.resolve_conflict(user_id=user_id, conflict_id=conflict_id, resolution=payload.resolution)
    if not resolved:
        raise HTTPException(status_code=404, detail='Conflict not found')
    return CalendarConflictDTO(id=resolved.id, description=resolved.description, status=resolved.status)


@router.post('/webhooks/google')
def ingest_google_webhook(
    payload: dict,
    x_webhook_secret: str | None = Header(default=None),
    x_calendar_user_id: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    settings = get_settings()
    if settings.google_calendar_webhook_secret and x_webhook_secret != settings.google_calendar_webhook_secret:
        raise HTTPException(status_code=401, detail='Invalid webhook secret')

    user_id = x_calendar_user_id or payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=400, detail='Missing user_id for webhook event ingestion')

    events = payload.get('events', [])
    if not isinstance(events, list):
        raise HTTPException(status_code=422, detail='Invalid events payload')

    repository = CalendarRepository(db)
    ingested_count = repository.ingest_webhook_events(user_id=user_id, events=events)
    today = datetime.now(timezone.utc).date().isoformat()
    conflicts = repository.generate_conflicts_for_day(user_id=user_id, day=today)

    return {
        'status': 'accepted',
        'user_id': str(user_id),
        'events_ingested': str(ingested_count),
        'conflicts_generated': str(len(conflicts)),
    }

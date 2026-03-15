from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.integrations.google_calendar import GoogleCalendarClient
from app.integrations.google_oauth import GoogleOAuthClient
from app.repositories.calendar import CalendarRepository


class CalendarSyncService:
    def __init__(
        self,
        db: Session,
        settings: Settings,
        calendar_client: GoogleCalendarClient | None = None,
        oauth_client: GoogleOAuthClient | None = None,
    ) -> None:
        self.db = db
        self.settings = settings
        self.calendar_client = calendar_client or GoogleCalendarClient()
        self.oauth_client = oauth_client or GoogleOAuthClient()
        self.repository = CalendarRepository(db)

    def sync_user_for_day(self, user_id: str, day: str) -> dict:
        token = self.repository.get_latest_google_token(user_id=user_id)
        if not token:
            rows = self.repository.touch_sync(user_id=user_id)
            return {
                'status': 'synced_fallback',
                'user_id': user_id,
                'accounts': len(rows),
                'events_ingested': 0,
                'conflicts_generated': 0,
            }

        token = self._refresh_if_needed(token)
        events = self.calendar_client.get_events_for_day(access_token=token.access_token, day=day)
        ingested = self.repository.upsert_events(account_id=token.account_id, events=events)
        self.repository.mark_account_synced(token.account_id)
        conflicts = self.repository.generate_conflicts_for_day(user_id=user_id, day=day)

        return {
            'status': 'synced',
            'user_id': user_id,
            'accounts': 1,
            'events_ingested': ingested,
            'conflicts_generated': len(conflicts),
        }

    def sync_all_users_for_today(self) -> dict:
        day = datetime.now(timezone.utc).date().isoformat()
        user_ids = self.repository.list_user_ids_with_google_tokens()

        summary = {
            'users_total': len(user_ids),
            'users_synced': 0,
            'events_ingested': 0,
            'conflicts_generated': 0,
        }

        for user_id in user_ids:
            result = self.sync_user_for_day(user_id=user_id, day=day)
            summary['users_synced'] += 1
            summary['events_ingested'] += int(result.get('events_ingested', 0))
            summary['conflicts_generated'] += int(result.get('conflicts_generated', 0))

        return summary

    def _refresh_if_needed(self, token):
        if not token.expires_at:
            return token

        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        refresh_threshold = datetime.now(timezone.utc) + timedelta(minutes=5)
        if expires_at > refresh_threshold:
            return token

        if not token.refresh_token or not self.settings.google_oauth_client_id or not self.settings.google_oauth_client_secret:
            return token

        try:
            refreshed = self.oauth_client.refresh_access_token(
                client_id=self.settings.google_oauth_client_id,
                client_secret=self.settings.google_oauth_client_secret,
                refresh_token=token.refresh_token,
            )
            return self.repository.update_token_record(
                token=token,
                access_token=refreshed.get('access_token', token.access_token),
                expires_in_seconds=refreshed.get('expires_in', 3600),
                refresh_token=refreshed.get('refresh_token', token.refresh_token),
                scope=refreshed.get('scope'),
                token_type=refreshed.get('token_type'),
            )
        except Exception:
            return token

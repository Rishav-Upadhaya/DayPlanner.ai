from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decrypt_token, encrypt_token
from app.models.calendar import CalendarAccount, CalendarConflict, CalendarEvent, CalendarOAuthToken


class CalendarRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_accounts(self, user_id: str) -> list[CalendarAccount]:
        stmt = (
            select(CalendarAccount)
            .where(
                CalendarAccount.user_id == user_id,
                CalendarAccount.email != 'webhook-ingest@google-calendar.local',
            )
            .order_by(CalendarAccount.email.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_or_create_account(self, user_id: str, provider: str, email: str) -> CalendarAccount:
        stmt = select(CalendarAccount).where(
            CalendarAccount.user_id == user_id,
            CalendarAccount.provider == provider,
            CalendarAccount.email == email,
        )
        account = self.db.scalar(stmt)
        if account:
            return account

        account = CalendarAccount(
            user_id=user_id,
            provider=provider,
            email=email,
            status='connected',
            last_synced_at=datetime.now(timezone.utc),
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def get_google_account_for_user(self, user_id: str) -> CalendarAccount | None:
        stmt = (
            select(CalendarAccount)
            .where(CalendarAccount.user_id == user_id, CalendarAccount.provider == 'google')
            .order_by(CalendarAccount.last_synced_at.desc().nulls_last())
        )
        return self.db.scalar(stmt)

    def upsert_google_token(
        self,
        user_id: str,
        email: str,
        access_token: str,
        refresh_token: str,
        scope: str,
        expires_in_seconds: int | None,
        token_type: str = 'Bearer',
    ) -> CalendarOAuthToken:
        account = self.get_or_create_account(user_id=user_id, provider='google', email=email)

        stmt = select(CalendarOAuthToken).where(CalendarOAuthToken.account_id == account.id)
        token = self.db.scalar(stmt)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds or 3600)

        if token:
            token.access_token = encrypt_token(access_token)
            token.refresh_token = encrypt_token(refresh_token) if refresh_token else token.refresh_token
            token.scope = scope
            token.token_type = token_type
            token.expires_at = expires_at
            token.updated_at = datetime.utcnow()
            self.db.add(token)
            self.db.commit()
            self.db.refresh(token)
            return token

        token = CalendarOAuthToken(
            account_id=account.id,
            access_token=encrypt_token(access_token),
            refresh_token=encrypt_token(refresh_token),
            scope=scope,
            token_type=token_type,
            expires_at=expires_at,
            updated_at=datetime.utcnow(),
        )
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_latest_google_token(self, user_id: str) -> CalendarOAuthToken | None:
        stmt = (
            select(CalendarOAuthToken)
            .join(CalendarAccount, CalendarAccount.id == CalendarOAuthToken.account_id)
            .where(CalendarAccount.user_id == user_id, CalendarAccount.provider == 'google')
            .order_by(CalendarOAuthToken.updated_at.desc())
        )
        token = self.db.scalar(stmt)
        if token:
            token.access_token = decrypt_token(token.access_token)
            token.refresh_token = decrypt_token(token.refresh_token)
        return token

    def list_user_ids_with_google_tokens(self) -> list[str]:
        stmt = (
            select(CalendarAccount.user_id)
            .join(CalendarOAuthToken, CalendarOAuthToken.account_id == CalendarAccount.id)
            .where(CalendarAccount.provider == 'google')
            .distinct()
        )
        return list(self.db.scalars(stmt).all())

    def update_token_record(
        self,
        token: CalendarOAuthToken,
        access_token: str,
        expires_in_seconds: int | None,
        refresh_token: str | None = None,
        scope: str | None = None,
        token_type: str | None = None,
    ) -> CalendarOAuthToken:
        token.access_token = encrypt_token(access_token)
        if refresh_token:
            token.refresh_token = encrypt_token(refresh_token)
        if scope:
            token.scope = scope
        if token_type:
            token.token_type = token_type
        token.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds or 3600)
        token.updated_at = datetime.utcnow()
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def upsert_events(self, account_id: str, events: list[dict]) -> int:
        upserted_count = 0
        for item in events:
            external_id = str(item.get('id', ''))
            if not external_id:
                continue

            starts_at = self._parse_datetime(item.get('starts_at'))
            ends_at = self._parse_datetime(item.get('ends_at'))
            if not starts_at or not ends_at:
                continue

            stmt = select(CalendarEvent).where(
                CalendarEvent.account_id == account_id,
                CalendarEvent.external_id == external_id,
            )
            existing = self.db.scalar(stmt)
            if existing:
                existing.title = str(item.get('title', existing.title))
                existing.starts_at = starts_at
                existing.ends_at = ends_at
                self.db.add(existing)
            else:
                self.db.add(
                    CalendarEvent(
                        account_id=account_id,
                        external_id=external_id,
                        title=str(item.get('title', 'Untitled event')),
                        starts_at=starts_at,
                        ends_at=ends_at,
                    )
                )
            upserted_count += 1

        self.db.commit()
        return upserted_count

    def touch_sync(self, user_id: str) -> list[CalendarAccount]:
        accounts = self.list_accounts(user_id=user_id)
        now = datetime.now(timezone.utc)
        for account in accounts:
            account.last_synced_at = now
            self.db.add(account)
        self.db.commit()
        for account in accounts:
            self.db.refresh(account)
        return accounts

    def mark_account_synced(self, account_id: str) -> None:
        stmt = select(CalendarAccount).where(CalendarAccount.id == account_id)
        account = self.db.scalar(stmt)
        if not account:
            return
        account.last_synced_at = datetime.now(timezone.utc)
        account.status = 'connected'
        self.db.add(account)
        self.db.commit()

    def list_conflicts(self, user_id: str, day: str) -> list[CalendarConflict]:
        target_day = date.fromisoformat(day)
        stmt = (
            select(CalendarConflict)
            .where(
                CalendarConflict.user_id == user_id,
                CalendarConflict.day == target_day,
                CalendarConflict.description.not_like('%Sample Calendar Event%'),
            )
            .order_by(CalendarConflict.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def generate_conflicts_for_day(self, user_id: str, day: str) -> list[CalendarConflict]:
        target_day = date.fromisoformat(day)
        events = self.list_events_for_day(user_id=user_id, day=day)

        self.db.query(CalendarConflict).filter(
            CalendarConflict.user_id == user_id,
            CalendarConflict.day == target_day,
        ).delete(synchronize_session=False)

        if len(events) < 2:
            self.db.commit()
            return []

        created: list[CalendarConflict] = []
        for index, first in enumerate(events):
            for second in events[index + 1:]:
                if not self._times_overlap(first.starts_at, first.ends_at, second.starts_at, second.ends_at):
                    continue

                description = (
                    f'Conflict on {day}: "{first.title}" '
                    f'({first.starts_at.strftime("%H:%M")}-{first.ends_at.strftime("%H:%M")}) overlaps '
                    f'with "{second.title}" ({second.starts_at.strftime("%H:%M")}-{second.ends_at.strftime("%H:%M")}).'
                )
                conflict = CalendarConflict(user_id=user_id, day=target_day, description=description, status='open')
                self.db.add(conflict)
                created.append(conflict)

        self.db.commit()
        for item in created:
            self.db.refresh(item)
        return created

    def resolve_conflict(self, user_id: str, conflict_id: str, resolution: str) -> CalendarConflict | None:
        stmt = select(CalendarConflict).where(CalendarConflict.id == conflict_id, CalendarConflict.user_id == user_id)
        conflict = self.db.scalar(stmt)
        if not conflict:
            return None
        conflict.status = f'resolved:{resolution}'
        self.db.add(conflict)
        self.db.commit()
        self.db.refresh(conflict)
        return conflict

    def list_events_for_day(self, user_id: str, day: str) -> list[CalendarEvent]:
        target_day = date.fromisoformat(day)
        day_start = datetime.combine(target_day, time.min).replace(tzinfo=timezone.utc)
        day_end = datetime.combine(target_day, time.max).replace(tzinfo=timezone.utc)

        stmt = (
            select(CalendarEvent)
            .join(CalendarAccount, CalendarAccount.id == CalendarEvent.account_id)
            .where(
                CalendarAccount.user_id == user_id,
                CalendarEvent.starts_at <= day_end,
                CalendarEvent.ends_at >= day_start,
            )
            .order_by(CalendarEvent.starts_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def ingest_webhook_events(self, user_id: str, events: list[dict]) -> int:
        account = self.get_google_account_for_user(user_id=user_id)
        if not account:
            return 0
        upserted = self.upsert_events(account_id=account.id, events=events)
        self.mark_account_synced(account.id)
        return upserted

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        normalized = value.replace('Z', '+00:00')
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _parse_hhmm(value: str) -> time:
        hours, minutes = value.split(':')
        return time(hour=int(hours), minute=int(minutes))

    @staticmethod
    def _times_overlap(start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> bool:
        return start1 < end2 and start2 < end1

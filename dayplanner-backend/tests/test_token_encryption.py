from uuid import uuid4

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.calendar import CalendarOAuthToken
from app.models.user import User
from app.repositories.calendar import CalendarRepository


def test_encrypt_decrypt_google_tokens(monkeypatch) -> None:
    monkeypatch.setenv('ENCRYPTION_KEY', '1' * 64)

    db = SessionLocal()
    try:
        user = User(
            email=f"enc-{uuid4().hex[:12]}@example.com",
            full_name='Encryption User',
            password_hash='hashed',
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        repository = CalendarRepository(db)
        repository.upsert_google_token(
            user_id=user.id,
            email=user.email,
            access_token='plain-access-token',
            refresh_token='plain-refresh-token',
            scope='calendar.readonly',
            expires_in_seconds=3600,
        )

        raw_stmt = (
            select(CalendarOAuthToken)
            .where(CalendarOAuthToken.account_id.is_not(None))
            .order_by(CalendarOAuthToken.updated_at.desc())
        )
        raw_token = db.scalar(raw_stmt)
        assert raw_token is not None
        assert raw_token.access_token != 'plain-access-token'
        assert raw_token.refresh_token != 'plain-refresh-token'

        latest = repository.get_latest_google_token(user_id=user.id)
        assert latest is not None
        assert latest.access_token == 'plain-access-token'
        assert latest.refresh_token == 'plain-refresh-token'
    finally:
        db.close()


def test_encrypt_decrypt_google_tokens_with_base64_key(monkeypatch) -> None:
    monkeypatch.setenv('ENCRYPTION_KEY', 'gIeVpEgmGdVkO0Q+GKIT2Lfh+Lq145MuADP/Nlmf0tU=')

    db = SessionLocal()
    try:
        user = User(
            email=f"enc-b64-{uuid4().hex[:12]}@example.com",
            full_name='Encryption User B64',
            password_hash='hashed',
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        repository = CalendarRepository(db)
        repository.upsert_google_token(
            user_id=user.id,
            email=user.email,
            access_token='plain-access-token',
            refresh_token='plain-refresh-token',
            scope='calendar.readonly',
            expires_in_seconds=3600,
        )

        latest = repository.get_latest_google_token(user_id=user.id)
        assert latest is not None
        assert latest.access_token == 'plain-access-token'
        assert latest.refresh_token == 'plain-refresh-token'
    finally:
        db.close()

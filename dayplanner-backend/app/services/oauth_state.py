from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.core.config import get_settings

ALGORITHM = 'HS256'


def create_oauth_state(*, purpose: str, user_id: str | None = None, ttl_seconds: int = 900) -> str:
    settings = get_settings()
    payload = {
        'purpose': purpose,
        'exp': datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds),
    }
    if user_id:
        payload['uid'] = user_id
    return jwt.encode(payload, settings.app_secret_key, algorithm=ALGORITHM)


def verify_oauth_state(*, token: str, expected_purpose: str, expected_user_id: str | None = None) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.app_secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError('Invalid OAuth state') from exc

    purpose = payload.get('purpose')
    if purpose != expected_purpose:
        raise ValueError('OAuth state purpose mismatch')

    if expected_user_id is not None:
        if payload.get('uid') != expected_user_id:
            raise ValueError('OAuth state user mismatch')

    return payload

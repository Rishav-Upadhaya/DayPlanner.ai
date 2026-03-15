from jose import JWTError, jwt
from fastapi import Header, HTTPException

from app.core.config import get_settings


def get_current_user_id(
    authorization: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
) -> str:
    settings = get_settings()
    if authorization and authorization.startswith('Bearer '):
        token = authorization.split(' ', 1)[1].strip()
        try:
            payload = jwt.decode(token, settings.app_secret_key, algorithms=['HS256'])
            subject = payload.get('sub')
            if isinstance(subject, str) and subject:
                return subject
        except JWTError as exc:
            if x_user_id and settings.app_env.lower() != 'production':
                return x_user_id
            raise HTTPException(status_code=401, detail='Invalid bearer token') from exc

    if x_user_id:
        return x_user_id

    raise HTTPException(status_code=401, detail='Missing authentication (Bearer token or X-User-Id)')

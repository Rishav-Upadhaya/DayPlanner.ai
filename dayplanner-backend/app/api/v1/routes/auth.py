from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user_id
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.integrations.google_oauth import GoogleOAuthClient
from app.repositories.users import UserAlreadyExistsError, UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, MeResponse, SignupRequest
from app.services.oauth_state import create_oauth_state, verify_oauth_state

router = APIRouter()
oauth_client = GoogleOAuthClient()


def _get_google_signin_redirect_uri() -> str:
    settings = get_settings()
    configured = settings.google_oauth_redirect_uri.strip()
    if configured:
        return configured
    return f"{settings.frontend_url.rstrip('/')}/auth"


@router.get('/google/start')
def google_start() -> dict[str, str]:
    settings = get_settings()
    if not settings.google_oauth_client_id:
        raise HTTPException(status_code=503, detail='Google OAuth is not configured: missing GOOGLE_OAUTH_CLIENT_ID')

    redirect_uri = _get_google_signin_redirect_uri()
    state = create_oauth_state(purpose='google_signin')
    redirect_url = oauth_client.build_auth_url(
        client_id=settings.google_oauth_client_id,
        redirect_uri=redirect_uri,
        scope='openid email profile',
        state=state,
    )
    return {'redirect_url': redirect_url, 'scope': 'openid email profile'}


@router.post('/signup', response_model=AuthResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user_repo = UserRepository(db)
    try:
        user = user_repo.create_local_user(email=payload.email, full_name=payload.full_name, password=payload.password)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail='User already exists') from exc
    return AuthResponse(access_token=create_access_token(subject=user.id), user_id=user.id)


@router.post('/login', response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user_repo = UserRepository(db)
    user = user_repo.authenticate_local_user(email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(status_code=401, detail='Invalid email or password')
    return AuthResponse(access_token=create_access_token(subject=user.id), user_id=user.id)


@router.get('/me', response_model=MeResponse)
def me(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> MeResponse:
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return MeResponse(user_id=user.id, email=user.email, full_name=user.full_name, avatar_url=user.avatar_url)


@router.get('/google/callback')
def google_callback(code: str, state: str, db: Session = Depends(get_db)) -> dict[str, str]:
    settings = get_settings()
    user_repo = UserRepository(db)

    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
        raise HTTPException(status_code=503, detail='Google OAuth is not configured')

    try:
        verify_oauth_state(token=state, expected_purpose='google_signin')
    except ValueError as exc:
        raise HTTPException(status_code=400, detail='Invalid OAuth state') from exc

    redirect_uri = _get_google_signin_redirect_uri()

    try:
        token_data = oauth_client.exchange_code(
            client_id=settings.google_oauth_client_id,
            client_secret=settings.google_oauth_client_secret,
            redirect_uri=redirect_uri,
            code=code,
        )
        user_info = oauth_client.get_user_info(access_token=token_data['access_token'])
        user = user_repo.get_or_create_google_user(
            email=user_info.get('email', ''),
            full_name=user_info.get('name', 'DayPlanner User'),
            google_sub=user_info.get('sub'),
            avatar_url=user_info.get('picture'),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail='Google OAuth exchange failed') from exc

    return {
        'access_token': create_access_token(subject=user.id),
        'refresh_token': token_data.get('refresh_token', ''),
        'token_type': 'bearer',
        'user_id': user.id,
    }

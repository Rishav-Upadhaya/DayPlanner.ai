from pydantic import BaseModel


class SignupRequest(BaseModel):
    email: str
    full_name: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user_id: str


class MeResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    avatar_url: str | None = None

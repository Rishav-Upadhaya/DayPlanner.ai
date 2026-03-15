from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_env: str = 'development'
    app_name: str = 'DayPlanner Backend'
    api_v1_prefix: str = '/api/v1'
    app_secret_key: str = 'change-me'
    app_access_token_expire_minutes: int = 60

    database_url: str = 'sqlite:///./dayplanner.db'

    openrouter_api_key: str = ''
    openrouter_model: str = 'openai/gpt-4o-mini'
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-1.5-flash'

    google_oauth_client_id: str = ''
    google_oauth_client_secret: str = ''
    google_oauth_redirect_uri: str = ''
    google_calendar_webhook_secret: str = ''
    frontend_url: str = 'http://localhost:3000'

    enable_background_sync: bool = False
    background_sync_interval_seconds: int = 300
    enable_background_sync_leader_lock: bool = True
    background_sync_leader_lock_id: int = 424242

    cors_allow_origins: str = 'http://localhost:3000,http://localhost:9002'


@lru_cache
def get_settings() -> Settings:
    return Settings()

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user_id
from app.core.database import get_db
from app.integrations.llm_client import get_openrouter_usage_pct, list_gemini_models, list_openrouter_models
from app.repositories.llm import LLMRepository
from app.repositories.settings import SettingsRepository
from app.schemas.llm import (
    LLMConfigDTO,
    LLMModelListRequest,
    LLMModelListResponse,
    LLMProviderListResponse,
    LLMProviderModel,
    LLMUsageCheckResponse,
    NotificationDTO,
)
from app.schemas.settings import SettingsDTO, SettingsUpdateDTO

router = APIRouter()


@router.get('', response_model=SettingsDTO)
def get_settings(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> SettingsDTO:
    repository = SettingsRepository(db)
    setting = repository.get_or_create(user_id=user_id)
    return SettingsDTO(
        timezone=setting.timezone,
        planning_style=setting.planning_style,
        morning_briefing_time=setting.morning_briefing_time,
        evening_checkin_time=setting.evening_checkin_time,
        notifications_enabled=True,
        privacy_mode='standard',
    )


@router.patch('', response_model=SettingsDTO)
def update_settings(
    payload: SettingsUpdateDTO,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> SettingsDTO:
    repository = SettingsRepository(db)
    setting = repository.get_or_create(user_id=user_id)
    updated = repository.update(setting=setting, data=payload.model_dump(exclude_none=True))
    return SettingsDTO(
        timezone=updated.timezone,
        planning_style=updated.planning_style,
        morning_briefing_time=updated.morning_briefing_time,
        evening_checkin_time=updated.evening_checkin_time,
        notifications_enabled=True,
        privacy_mode='standard',
    )


@router.get('/notifications', response_model=list[NotificationDTO])
def list_notifications(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> list[NotificationDTO]:
    repository = LLMRepository(db)
    rows = repository.list_notifications(user_id=user_id)
    return [
        NotificationDTO(
            id=item.id,
            kind=item.kind,
            message=item.message,
            is_read=item.is_read,
            created_at=item.created_at.isoformat(),
        )
        for item in rows
    ]


@router.get('/llm/providers', response_model=LLMProviderListResponse)
def llm_providers() -> LLMProviderListResponse:
    return LLMProviderListResponse(providers=['openrouter', 'gemini'])


@router.post('/llm/models', response_model=LLMModelListResponse)
def llm_models(payload: LLMModelListRequest) -> LLMModelListResponse:
    provider = payload.provider.lower().strip()
    try:
        if provider == 'openrouter':
            models = list_openrouter_models(api_key=payload.api_key)
        elif provider == 'gemini':
            models = list_gemini_models(api_key=payload.api_key)
        else:
            raise HTTPException(status_code=422, detail='Unsupported provider')
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail='Unable to list models for provided API key') from exc

    return LLMModelListResponse(provider=provider, models=[LLMProviderModel(**item) for item in models])


@router.get('/llm/config', response_model=LLMConfigDTO)
def get_llm_config(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> LLMConfigDTO:
    repository = LLMRepository(db)
    config = repository.get_or_create_config(user_id=user_id)
    return LLMConfigDTO(
        primary_provider=config.primary_provider,
        primary_api_key=config.primary_api_key,
        primary_model=config.primary_model,
        fallback_provider=config.fallback_provider,
        fallback_api_key=config.fallback_api_key,
        fallback_model=config.fallback_model,
        usage_alert_enabled=config.usage_alert_enabled,
        usage_alert_threshold_pct=config.usage_alert_threshold_pct,
    )


@router.put('/llm/config', response_model=LLMConfigDTO)
def set_llm_config(payload: LLMConfigDTO, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> LLMConfigDTO:
    repository = LLMRepository(db)
    config = repository.get_or_create_config(user_id=user_id)
    updated = repository.update_config(config=config, data=payload.model_dump())
    return LLMConfigDTO(
        primary_provider=updated.primary_provider,
        primary_api_key=updated.primary_api_key,
        primary_model=updated.primary_model,
        fallback_provider=updated.fallback_provider,
        fallback_api_key=updated.fallback_api_key,
        fallback_model=updated.fallback_model,
        usage_alert_enabled=updated.usage_alert_enabled,
        usage_alert_threshold_pct=updated.usage_alert_threshold_pct,
    )


@router.post('/llm/usage-check', response_model=LLMUsageCheckResponse)
def llm_usage_check(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> LLMUsageCheckResponse:
    repository = LLMRepository(db)
    config = repository.get_or_create_config(user_id=user_id)

    usage_pct = 0.0
    alert_triggered = False

    if config.primary_provider == 'openrouter' and config.primary_api_key:
        try:
            usage_pct = get_openrouter_usage_pct(api_key=config.primary_api_key)
        except Exception:
            usage_pct = 0.0

        if config.usage_alert_enabled and usage_pct >= float(config.usage_alert_threshold_pct):
            repository.create_notification(
                user_id=user_id,
                kind='warning',
                message=f'OpenRouter API usage is at {usage_pct:.1f}% of your limit. Consider switching to fallback provider.',
            )
            alert_triggered = True

    return LLMUsageCheckResponse(provider=config.primary_provider, usage_pct=usage_pct, alert_triggered=alert_triggered)

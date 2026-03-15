from pydantic import BaseModel


class LLMProviderModel(BaseModel):
    id: str
    name: str


class LLMProviderListResponse(BaseModel):
    providers: list[str]


class LLMModelListRequest(BaseModel):
    provider: str
    api_key: str


class LLMModelListResponse(BaseModel):
    provider: str
    models: list[LLMProviderModel]


class LLMConfigDTO(BaseModel):
    primary_provider: str
    primary_api_key: str
    primary_model: str
    fallback_provider: str
    fallback_api_key: str
    fallback_model: str
    usage_alert_enabled: bool
    usage_alert_threshold_pct: int


class LLMUsageCheckResponse(BaseModel):
    provider: str
    usage_pct: float
    alert_triggered: bool


class NotificationDTO(BaseModel):
    id: str
    kind: str
    message: str
    is_read: bool
    created_at: str

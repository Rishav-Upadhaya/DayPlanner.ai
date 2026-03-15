from pydantic import BaseModel


class SettingsDTO(BaseModel):
    timezone: str = 'UTC'
    planning_style: str = 'balanced'
    morning_briefing_time: str = '07:30'
    evening_checkin_time: str = '20:00'
    notifications_enabled: bool = True
    privacy_mode: str = 'standard'


class SettingsUpdateDTO(BaseModel):
    timezone: str | None = None
    planning_style: str | None = None
    morning_briefing_time: str | None = None
    evening_checkin_time: str | None = None
    notifications_enabled: bool | None = None
    privacy_mode: str | None = None

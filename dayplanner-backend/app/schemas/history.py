from pydantic import BaseModel


class HistorySummaryDTO(BaseModel):
    completion_rate: float
    streak_days: int
    memory_patterns_count: int


class WeeklyPointDTO(BaseModel):
    day: str
    completion: int

from pydantic import BaseModel


class CalendarAccountDTO(BaseModel):
    id: str
    provider: str
    email: str
    status: str
    last_synced_at: str | None = None


class CalendarConflictDTO(BaseModel):
    id: str
    description: str
    status: str

from pydantic import BaseModel, Field


class PlanBlockDTO(BaseModel):
    id: str | None = None
    title: str
    start_time: str
    end_time: str
    priority: str = 'medium'
    category: str = 'work'
    completed: bool = False


class PlanDTO(BaseModel):
    id: str | None = None
    date: str
    summary: str = ''
    blocks: list[PlanBlockDTO] = Field(default_factory=list)


class GeneratePlanRequest(BaseModel):
    user_input: str
    date_for_plan: str

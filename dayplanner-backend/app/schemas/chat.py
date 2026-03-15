from pydantic import BaseModel, Field

from app.schemas.plan import PlanBlockDTO


class ChatMessageCreate(BaseModel):
    content: str
    plan_date: str | None = None


class ChatMessageDTO(BaseModel):
    id: str
    role: str
    content: str


class ChatResponseDTO(BaseModel):
    message: str
    summary: str = ''
    assistant_reply: str = ''
    saved_to_today: bool = False
    needs_clarification: bool = False
    follow_up_questions: list[str] = Field(default_factory=list)
    blocks: list[PlanBlockDTO] = Field(default_factory=list)

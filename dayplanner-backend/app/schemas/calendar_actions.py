from pydantic import BaseModel


class ConflictResolutionRequest(BaseModel):
    resolution: str = 'accept_ai_suggestion'

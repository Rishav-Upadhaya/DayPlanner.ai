from pydantic import BaseModel


class MemoryItemDTO(BaseModel):
    id: str
    node_type: str
    content: str
    confidence: str


class MemoryCreateDTO(BaseModel):
    node_type: str = 'note'
    content: str
    confidence: str = 'medium'


class MemoryContextResponse(BaseModel):
    snippets: list[str]
    items: list[MemoryItemDTO]

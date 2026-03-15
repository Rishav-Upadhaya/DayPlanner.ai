from typing import Annotated, Any

from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    user_id: str
    session_id: str
    plan_date: str
    llm_config: dict[str, str]
    messages: Annotated[list[dict[str, str]], add_messages]
    user_input: str
    intent: str
    entities: dict[str, Any]
    memory_snippets: list[str]
    existing_calendar_events: list[dict[str, str]]
    previous_day_summary: str
    previous_day_blocks: list[dict[str, Any]]
    recent_messages: list[dict[str, str]]
    assistant_reply: str
    summary: str
    blocks: list[dict[str, Any]]
    save_to_today: bool
    needs_clarification: bool
    follow_up_questions: list[str]
    error: str | None

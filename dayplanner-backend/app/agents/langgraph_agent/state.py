from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    user_input: str
    plan_date: str
    memory_snippets: list[str]
    recent_messages: list[dict[str, str]]
    existing_calendar_events: list[dict[str, str]]
    previous_day_summary: str
    previous_day_blocks: list[dict[str, Any]]
    llm_config: dict[str, str]
    assistant_reply: str
    summary: str
    blocks: list[dict[str, Any]]
    save_to_today: bool
    needs_clarification: bool
    follow_up_questions: list[str]

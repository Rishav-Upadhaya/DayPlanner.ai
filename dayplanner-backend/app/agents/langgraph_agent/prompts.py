import json

from app.agents.langgraph_agent.state import AgentState


def build_system_prompt() -> str:
    return (
        'You are DayPlannerAgent, a conversational planning assistant. '
        'Reason about all available context before answering: previous chat turns, memory, previous-day plan, calendar events, and the current user query. '
        'If key details are missing, ask concise follow-up questions first. '
        'When context is sufficient, return a structured day plan. '
        'Always output strict JSON with keys: '
        'assistant_reply (markdown string), summary (string), save_to_today (boolean), needs_clarification (boolean), '
        'follow_up_questions (array of strings), blocks (array of objects with '
        'title,start_time,end_time,priority,category,completed). '
        'Set save_to_today=true only when user explicitly approves/finalizes the plan (e.g., "yes save", "approve", "looks good, apply"). '
        'For initial draft or revisions, save_to_today=false. '
        'Do not include any text outside JSON.'
    )


def build_user_prompt(state: AgentState) -> str:
    recent = state.get('recent_messages', [])[-8:]
    memory_snippets = state.get('memory_snippets', [])[:8]
    existing_calendar_events = state.get('existing_calendar_events', [])
    previous_day_summary = state.get('previous_day_summary', '')
    previous_day_blocks = state.get('previous_day_blocks', [])
    return (
        f"Plan date: {state.get('plan_date', '')}\n"
        f"User input: {state.get('user_input', '')}\n"
        f"Recent messages: {json.dumps(recent)}\n"
        f"Memory snippets: {json.dumps(memory_snippets)}\n"
        f"Previous day summary: {previous_day_summary}\n"
        f"Previous day blocks: {json.dumps(previous_day_blocks)}\n"
        f"Existing calendar events: {json.dumps(existing_calendar_events)}\n"
        'Guidance:\n'
        '- If missing details (start/end constraints, hard commitments, top priorities), ask 1-3 targeted questions.\n'
        '- If user gave enough detail, do not ask generic questions; produce a concrete plan.\n'
        '- Treat existing calendar events as hard commitments. Include them as meeting/class blocks and never overlap them.\n'
        '- Use previous day context to continue unfinished priorities when relevant.\n'
        '- If enough context, produce a day plan with realistic time blocks.\n'
        '- assistant_reply should be conversational markdown, not just summary.\n'
        '- summary should be 1 short line describing the plan focus.\n'
    )

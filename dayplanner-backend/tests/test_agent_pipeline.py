from app.agents.dayplanner_agent import DayPlannerAgent


def test_agent_pipeline_routes_and_returns_plan(monkeypatch) -> None:
    agent = DayPlannerAgent()

    def fake_generate(**kwargs):
        system_prompt = kwargs.get('system_prompt', '')
        if 'Classify the user\'s planning intent' in system_prompt:
            return '{"intent":"new_plan","entities":{"tasks":["report"],"times":[],"date":"today"}}'
        return (
            '{'
            '"assistant_reply":"Here is your generated plan.",'
            '"summary":"Generated daily plan",'
            '"needs_clarification":false,'
            '"follow_up_questions":[],'
            '"save_to_today":true,'
            '"blocks":['
            '{"title":"Report","start_time":"09:00","end_time":"10:00","priority":"high","category":"work","completed":false}'
            ']'
            '}'
        )

    monkeypatch.setattr(agent.llm, 'generate', fake_generate)

    result = agent.run(
        user_input='Plan my day around writing report',
        plan_date='2026-03-15',
        memory_snippets=[],
        recent_messages=[],
        existing_calendar_events=[],
        llm_config={},
        user_id='u-1',
        session_id='s-1',
    )

    assert result['summary'] == 'Generated daily plan'
    assert result['save_to_today'] is True
    assert len(result['blocks']) == 1


def test_agent_pipeline_follow_up_path(monkeypatch) -> None:
    agent = DayPlannerAgent()

    def fake_generate(**kwargs):
        system_prompt = kwargs.get('system_prompt', '')
        if 'Classify the user\'s planning intent' in system_prompt:
            return '{"intent":"follow_up","entities":{}}'
        return (
            '{'
            '"assistant_reply":"Nice progress today!",'
            '"summary":"Follow up complete",'
            '"needs_clarification":false,'
            '"follow_up_questions":[],'
            '"save_to_today":false,'
            '"blocks":[]'
            '}'
        )

    monkeypatch.setattr(agent.llm, 'generate', fake_generate)

    result = agent.run(
        user_input='I completed most tasks',
        plan_date='2026-03-15',
        memory_snippets=[],
        recent_messages=[{'role': 'user', 'content': 'I completed most tasks'}],
        existing_calendar_events=[],
        llm_config={},
        user_id='u-1',
        session_id='s-1',
    )

    assert result['summary'] == 'Follow up complete'
    assert result['needs_clarification'] is False

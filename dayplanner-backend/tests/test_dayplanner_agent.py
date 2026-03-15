from app.agents.dayplanner_agent import DayPlannerAgent


def test_agent_fallback_asks_clarification_for_sparse_input(monkeypatch) -> None:
    agent = DayPlannerAgent()
    monkeypatch.setattr(agent.llm, 'generate', lambda **_: (_ for _ in ()).throw(RuntimeError('llm down')))

    result = agent.run(
        user_input='help',
        plan_date='2026-03-15',
        memory_snippets=[],
        recent_messages=[],
        existing_calendar_events=[],
        llm_config={},
    )

    assert result['needs_clarification'] is True
    assert len(result['follow_up_questions']) >= 1
    assert result['blocks'] == []


def test_agent_fallback_returns_blocks_when_context_present(monkeypatch) -> None:
    agent = DayPlannerAgent()
    monkeypatch.setattr(agent.llm, 'generate', lambda **_: (_ for _ in ()).throw(RuntimeError('llm down')))

    result = agent.run(
        user_input='I need to finish project report and have meeting at 11:00',
        plan_date='2026-03-15',
        memory_snippets=['User prefers deep work before noon'],
        recent_messages=[{'role': 'user', 'content': 'Plan my day'}],
        existing_calendar_events=[],
        llm_config={},
    )

    assert result['needs_clarification'] is False
    assert len(result['blocks']) >= 1
    assert result['summary']


def test_agent_enforces_calendar_events(monkeypatch) -> None:
    agent = DayPlannerAgent()

    llm_payload = (
        '{'
        '"assistant_reply":"Here is your plan.",' 
        '"summary":"Plan with constraints",'
        '"needs_clarification":false,'
        '"follow_up_questions":[],'
        '"blocks":['
        '{"title":"Deep work","start_time":"09:30","end_time":"10:30","priority":"high","category":"work","completed":false},'
        '{"title":"Email","start_time":"11:30","end_time":"12:00","priority":"low","category":"work","completed":false}'
        ']'
        '}'
    )
    monkeypatch.setattr(agent.llm, 'generate', lambda **_: llm_payload)

    result = agent.run(
        user_input='Plan my day',
        plan_date='2026-03-15',
        memory_snippets=[],
        recent_messages=[],
        existing_calendar_events=[
            {
                'id': 'evt-1',
                'title': 'Team Sync',
                'date': '2026-03-15',
                'start_time': '09:00',
                'end_time': '10:00',
            }
        ],
        llm_config={},
    )

    assert any(block['title'] == 'Team Sync' for block in result['blocks'])
    assert all(block['title'] != 'Deep work' for block in result['blocks'])


def test_agent_fallback_enforces_calendar_events(monkeypatch) -> None:
    agent = DayPlannerAgent()
    monkeypatch.setattr(agent.llm, 'generate', lambda **_: (_ for _ in ()).throw(RuntimeError('llm down')))

    result = agent.run(
        user_input='Plan my day from 08:00 to 18:00 with coding and review tasks',
        plan_date='2026-03-15',
        memory_snippets=[],
        recent_messages=[],
        existing_calendar_events=[
            {
                'id': 'evt-1',
                'title': 'Daily Standup',
                'date': '2026-03-15',
                'start_time': '09:00',
                'end_time': '09:30',
            }
        ],
        llm_config={},
    )

    assert any(block['title'] == 'Daily Standup' for block in result['blocks'])
    assert all(block['title'] != 'Priority Focus Block' for block in result['blocks'])


def test_agent_meeting_query_uses_calendar_events(monkeypatch) -> None:
    agent = DayPlannerAgent()
    monkeypatch.setattr(agent.llm, 'generate', lambda **_: (_ for _ in ()).throw(RuntimeError('llm down')))

    result = agent.run(
        user_input='Do I have meetings today?',
        plan_date='2026-03-15',
        memory_snippets=[],
        recent_messages=[],
        existing_calendar_events=[
            {
                'id': 'evt-1',
                'title': 'Design Review',
                'date': '2026-03-15',
                'start_time': '10:00',
                'end_time': '10:30',
            }
        ],
        llm_config={},
    )

    assert result['needs_clarification'] is False
    assert 'Design Review' in result['assistant_reply']
    assert any(block['title'] == 'Design Review' for block in result['blocks'])


def test_agent_meeting_query_with_no_events(monkeypatch) -> None:
    agent = DayPlannerAgent()
    monkeypatch.setattr(agent.llm, 'generate', lambda **_: (_ for _ in ()).throw(RuntimeError('llm down')))

    result = agent.run(
        user_input='Do I have meetings today?',
        plan_date='2026-03-15',
        memory_snippets=[],
        recent_messages=[],
        existing_calendar_events=[],
        llm_config={},
    )

    assert result['needs_clarification'] is False
    assert 'do not see any synced meetings' in result['assistant_reply'].lower()


def test_agent_fallback_parses_recurring_class_and_task_list(monkeypatch) -> None:
    agent = DayPlannerAgent()
    monkeypatch.setattr(agent.llm, 'generate', lambda **_: (_ for _ in ()).throw(RuntimeError('llm down')))

    query = (
        'I have classes everyday from Sunday to friday from 6:30 am to 9:30 am. '
        'I need to do things like research on med captioning, final year project contextwatch, '
        'Astergaze company work and tasks.'
    )

    result = agent.run(
        user_input=query,
        plan_date='2026-03-15',
        memory_snippets=[],
        recent_messages=[],
        existing_calendar_events=[],
        llm_config={},
    )

    titles = [item['title'].lower() for item in result['blocks']]
    assert result['needs_clarification'] is False
    assert any('class schedule' in title for title in titles)
    assert any('research on med captioning' in title for title in titles)
    assert any('contextwatch' in title for title in titles)
    assert any('astergaze' in title for title in titles)

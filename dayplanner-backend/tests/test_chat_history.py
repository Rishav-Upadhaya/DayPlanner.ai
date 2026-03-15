def test_get_session_messages_returns_message_history(client, auth_headers, monkeypatch) -> None:
    from app.api.v1.routes import chat as chat_route

    monkeypatch.setattr(chat_route.dayplanner_agent, 'run', lambda **_: {
        'assistant_reply': 'Test reply',
        'summary': 'Test',
        'needs_clarification': False,
        'follow_up_questions': [],
        'save_to_today': False,
        'blocks': [],
    })

    session = client.post('/api/v1/chat/sessions', headers=auth_headers).json()
    session_id = session['session_id']

    client.post(
        f'/api/v1/chat/sessions/{session_id}/messages',
        headers=auth_headers,
        json={'content': 'Plan my day', 'plan_date': '2026-03-15'},
    )

    response = client.get(f'/api/v1/chat/sessions/{session_id}/messages', headers=auth_headers)
    assert response.status_code == 200
    messages = response.json()
    assert any(message['role'] == 'user' and 'Plan my day' in message['content'] for message in messages)
    assert any(message['role'] == 'assistant' and 'Test reply' in message['content'] for message in messages)


def test_force_save_plan(client, auth_headers) -> None:
    response = client.post(
        '/api/v1/plans/force-save',
        headers=auth_headers,
        json={
            'date_for_plan': '2026-03-15',
            'summary': 'Approved plan',
            'force_blocks': [
                {
                    'title': 'Work',
                    'start_time': '09:00',
                    'end_time': '10:00',
                    'priority': 'high',
                    'category': 'work',
                    'completed': False,
                    'agent_note': 'Keep distractions off.',
                }
            ],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload['summary'] == 'Approved plan'
    assert payload['blocks'][0]['agent_note'] == 'Keep distractions off.'

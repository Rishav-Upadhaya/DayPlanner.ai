from app.api.v1.routes import chat as chat_route


def test_stream_endpoint_returns_sse_content_type(client, auth_headers, monkeypatch) -> None:
    monkeypatch.setattr(
        chat_route.dayplanner_agent,
        'run',
        lambda **_: {
            'assistant_reply': 'Streaming response for plan.',
            'summary': 'Plan summary',
            'needs_clarification': False,
            'follow_up_questions': [],
            'save_to_today': True,
            'blocks': [
                {
                    'title': 'Focus Block',
                    'start_time': '09:00',
                    'end_time': '10:00',
                    'priority': 'high',
                    'category': 'work',
                    'completed': False,
                }
            ],
        },
    )

    session = client.post('/api/v1/chat/sessions', headers=auth_headers).json()

    with client.stream(
        'POST',
        f"/api/v1/chat/sessions/{session['session_id']}/messages/stream",
        headers=auth_headers,
        json={'content': 'Plan my day', 'plan_date': '2026-03-15'},
    ) as response:
        assert response.status_code == 200
        assert 'text/event-stream' in response.headers['content-type']
        assert response.headers.get('x-accel-buffering') == 'no'
        first_line = next(response.iter_lines())
        assert first_line.startswith('data:')

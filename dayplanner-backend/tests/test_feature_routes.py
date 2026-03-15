from app.api.v1.routes import chat as chat_route
from app.api.v1.routes import settings as settings_route
from app.core.config import get_settings

def test_auth_me_endpoint(client, auth_headers) -> None:
    response = client.get('/api/v1/auth/me', headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload['user_id']
    assert payload['email'].endswith('@example.com')


def test_chat_endpoint(client, auth_headers, monkeypatch) -> None:
    monkeypatch.setattr(
        chat_route.dayplanner_agent,
        'run',
        lambda **_: {
            'assistant_reply': '### Plan\n- Block 1\n- Block 2',
            'summary': 'Chat produced plan summary',
            'needs_clarification': False,
            'follow_up_questions': [],
            'blocks': [
                {
                    'title': 'Plan Tasks',
                    'start_time': '09:00',
                    'end_time': '10:00',
                    'priority': 'high',
                    'category': 'work',
                    'completed': False,
                }
            ],
        },
    )

    session_response = client.post('/api/v1/chat/sessions', headers=auth_headers)
    assert session_response.status_code == 200
    session_id = session_response.json()['session_id']

    response = client.post(
        f'/api/v1/chat/sessions/{session_id}/messages',
        headers=auth_headers,
        json={'content': 'Plan my day', 'plan_date': '2026-03-15'},
    )
    assert response.status_code == 200
    assert response.json()['summary'] == 'Chat produced plan summary'
    assert response.json()['assistant_reply'].startswith('### Plan')

    list_response = client.get('/api/v1/chat/sessions', headers=auth_headers)
    assert list_response.status_code == 200
    assert any(item['id'] == session_id for item in list_response.json())


def test_calendar_conflicts_endpoint(client, auth_headers) -> None:
    response = client.get('/api/v1/calendar/conflicts?date=2026-03-14', headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    sync_response = client.post('/api/v1/calendar/sync-all', headers=auth_headers)
    assert sync_response.status_code == 200
    assert sync_response.json()['status'] in {'synced', 'synced_fallback'}

    refreshed_response = client.get('/api/v1/calendar/conflicts?date=2026-03-14', headers=auth_headers)
    assert refreshed_response.status_code == 200
    conflicts = refreshed_response.json()
    if conflicts:
        conflict_id = conflicts[0]['id']
        resolve_response = client.post(
            f'/api/v1/calendar/conflicts/{conflict_id}/resolve',
            headers=auth_headers,
            json={'resolution': 'accept_ai_suggestion'},
        )
        assert resolve_response.status_code == 200
        assert 'resolved' in resolve_response.json()['status']


def test_settings_patch_and_llm_config(client, auth_headers, monkeypatch) -> None:
    response = client.patch('/api/v1/settings', headers=auth_headers, json={'planning_style': 'deep_work', 'timezone': 'UTC'})
    assert response.status_code == 200
    assert response.json()['planning_style'] == 'deep_work'

    providers_response = client.get('/api/v1/settings/llm/providers', headers=auth_headers)
    assert providers_response.status_code == 200
    assert 'openrouter' in providers_response.json()['providers']

    monkeypatch.setattr(settings_route, 'list_openrouter_models', lambda api_key: [{'id': 'm1', 'name': 'Model One'}])
    models_response = client.post(
        '/api/v1/settings/llm/models',
        headers=auth_headers,
        json={'provider': 'openrouter', 'api_key': 'sk-or-v1-test-key'},
    )
    assert models_response.status_code == 200
    assert models_response.json()['models'][0]['id'] == 'm1'

    config_payload = {
        'primary_provider': 'openrouter',
        'primary_api_key': 'sk-or-v1-test-key',
        'primary_model': 'openai/gpt-4o-mini',
        'fallback_provider': 'gemini',
        'fallback_api_key': 'AIzaSyD-test-key',
        'fallback_model': 'gemini-1.5-flash',
        'usage_alert_enabled': True,
        'usage_alert_threshold_pct': 40,
    }
    config_response = client.put('/api/v1/settings/llm/config', headers=auth_headers, json=config_payload)
    assert config_response.status_code == 200
    assert config_response.json()['primary_provider'] == 'openrouter'

    monkeypatch.setattr(settings_route, 'get_openrouter_usage_pct', lambda api_key: 82.0)
    usage_response = client.post('/api/v1/settings/llm/usage-check', headers=auth_headers)
    assert usage_response.status_code == 200
    assert usage_response.json()['alert_triggered'] is True

    notifications_response = client.get('/api/v1/settings/notifications', headers=auth_headers)
    assert notifications_response.status_code == 200
    assert any('OpenRouter API usage' in item['message'] for item in notifications_response.json())


def test_memory_crud(client, auth_headers) -> None:
    read_response = client.get('/api/v1/memory/context', headers=auth_headers)
    assert read_response.status_code == 200
    assert 'items' in read_response.json()

    add_response = client.post(
        '/api/v1/memory/context',
        headers=auth_headers,
        json={'node_type': 'note', 'content': 'I prefer focus blocks', 'confidence': 'high'},
    )
    assert add_response.status_code == 200
    memory_id = add_response.json()['id']

    delete_response = client.delete(f'/api/v1/memory/context/{memory_id}', headers=auth_headers)
    assert delete_response.status_code == 200

    reset_response = client.post('/api/v1/memory/reset', headers=auth_headers)
    assert reset_response.status_code == 200
    assert reset_response.json()['status'] == 'memory_reset_completed'


def test_history_endpoints(client, auth_headers) -> None:
    summary_response = client.get('/api/v1/history/summary?range=7d', headers=auth_headers)
    assert summary_response.status_code == 200
    assert 'completion_rate' in summary_response.json()

    weekly_response = client.get('/api/v1/history/weekly-performance', headers=auth_headers)
    assert weekly_response.status_code == 200
    assert isinstance(weekly_response.json(), list)

    plans_response = client.get('/api/v1/history/plans', headers=auth_headers)
    assert plans_response.status_code == 200
    assert isinstance(plans_response.json(), list)


def test_calendar_webhook_ingestion(client, auth_headers) -> None:
    user_id = auth_headers['X-User-Id']
    settings = get_settings()
    payload = {
        'user_id': user_id,
        'events': [
            {
                'id': 'webhook-event-1',
                'title': 'Webhook Meeting',
                'starts_at': '2026-03-15T10:00:00+00:00',
                'ends_at': '2026-03-15T10:30:00+00:00',
            }
        ],
    }
    headers = {}
    if settings.google_calendar_webhook_secret:
        headers['X-Webhook-Secret'] = settings.google_calendar_webhook_secret
    response = client.post('/api/v1/calendar/webhooks/google', headers=headers, json=payload)
    assert response.status_code == 200
    assert response.json()['status'] == 'accepted'

from app.api.v1.routes import plans as plans_route

def test_generate_plan(client, auth_headers, monkeypatch) -> None:
    monkeypatch.setattr(
        plans_route.planning_graph,
        'run',
        lambda **_: {
            'summary': 'Focused day with one key block',
            'blocks': [
                {
                    'title': 'Deep Work',
                    'start_time': '09:00',
                    'end_time': '10:30',
                    'priority': 'high',
                    'category': 'work',
                    'completed': False,
                }
            ],
        },
    )

    response = client.post(
        '/api/v1/plans/generate',
        headers=auth_headers,
        json={'user_input': 'I need deep work and gym', 'date_for_plan': '2026-03-14'},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload['date'] == '2026-03-14'
    assert len(payload['blocks']) > 0
    assert payload['summary'] == 'Focused day with one key block'


def test_update_plan_block_and_evening_checkin(client, auth_headers, monkeypatch) -> None:
    monkeypatch.setattr(
        plans_route.planning_graph,
        'run',
        lambda **_: {
            'summary': 'Generated plan for checkin',
            'blocks': [
                {
                    'title': 'Focus Sprint',
                    'start_time': '08:00',
                    'end_time': '09:00',
                    'priority': 'high',
                    'category': 'work',
                    'completed': False,
                },
                {
                    'title': 'Team Sync',
                    'start_time': '10:00',
                    'end_time': '10:30',
                    'priority': 'medium',
                    'category': 'meeting',
                    'completed': False,
                },
            ],
        },
    )

    create_response = client.post(
        '/api/v1/plans/generate',
        headers=auth_headers,
        json={'user_input': 'Build a plan', 'date_for_plan': '2026-03-15'},
    )
    assert create_response.status_code == 200
    plan_payload = create_response.json()

    first_block_id = plan_payload['blocks'][0]['id']
    update_response = client.patch(
        f"/api/v1/plans/{plan_payload['id']}/blocks/{first_block_id}?completed=true",
        headers=auth_headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()['completed'] is True

    checkin_response = client.post(f"/api/v1/plans/{plan_payload['id']}/evening-checkin", headers=auth_headers)
    assert checkin_response.status_code == 200
    assert checkin_response.json()['status'] == 'recorded'
    assert checkin_response.json()['completion_pct'] == '50'


def test_today_plan_requires_auth_header(client) -> None:
    response = client.get('/api/v1/plans/today?date=2026-03-14')
    assert response.status_code == 401

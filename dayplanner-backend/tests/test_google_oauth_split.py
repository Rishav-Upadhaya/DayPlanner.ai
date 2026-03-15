from urllib.parse import parse_qs, urlparse


def _query_params(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)


def test_google_signin_scope_is_identity_only(client) -> None:
    response = client.get('/api/v1/auth/google/start')
    assert response.status_code == 200
    payload = response.json()
    params = _query_params(payload['redirect_url'])
    scope = params.get('scope', [''])[0]

    assert 'openid' in scope
    assert 'email' in scope
    assert 'profile' in scope
    assert 'calendar.readonly' not in scope


def test_google_calendar_scope_is_calendar_only(client, auth_headers) -> None:
    response = client.post('/api/v1/calendar/accounts/google/start', headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    params = _query_params(payload['redirect_url'])
    scope = params.get('scope', [''])[0]

    assert 'calendar.readonly' in scope
    assert 'calendar.events.readonly' in scope

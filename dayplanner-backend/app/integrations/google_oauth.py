from urllib.parse import urlencode

import httpx


class GoogleOAuthClient:
    AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
    TOKEN_URL = 'https://oauth2.googleapis.com/token'
    USERINFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'

    def build_auth_url(
        self,
        client_id: str,
        redirect_uri: str,
        scope: str,
        state: str,
        *,
        login_hint: str | None = None,
        extra_params: dict[str, str] | None = None,
    ) -> str:
        params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': scope,
            'access_type': 'offline',
            'prompt': 'consent',
            'state': state,
        }
        if login_hint:
            params['login_hint'] = login_hint
        if extra_params:
            params.update(extra_params)

        query = urlencode(params)
        return f'{self.AUTH_URL}?{query}'

    def exchange_code(self, client_id: str, client_secret: str, redirect_uri: str, code: str) -> dict:
        response = httpx.post(
            self.TOKEN_URL,
            data={
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def refresh_access_token(self, client_id: str, client_secret: str, refresh_token: str) -> dict:
        response = httpx.post(
            self.TOKEN_URL,
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token',
            },
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

    def get_user_info(self, access_token: str) -> dict:
        response = httpx.get(
            self.USERINFO_URL,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=20,
        )
        response.raise_for_status()
        return response.json()

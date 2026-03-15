import re
from typing import NamedTuple


class ApiKeyCheckResult(NamedTuple):
    provider: str
    present: bool
    looks_valid: bool
    masked_value: str
    note: str


def mask_secret(value: str, visible_prefix: int = 6, visible_suffix: int = 4) -> str:
    if not value:
        return ''
    if len(value) <= visible_prefix + visible_suffix:
        return '*' * len(value)
    return f"{value[:visible_prefix]}{'*' * (len(value) - visible_prefix - visible_suffix)}{value[-visible_suffix:]}"


def check_openrouter_key(value: str | None) -> ApiKeyCheckResult:
    key = (value or '').strip()
    if not key:
        return ApiKeyCheckResult('openrouter', False, False, '', 'Missing OPENROUTER_API_KEY')

    looks_valid = bool(re.fullmatch(r'sk-or-v1-[A-Za-z0-9]{32,}', key))
    note = 'Format looks valid' if looks_valid else 'Unexpected OpenRouter key format'
    return ApiKeyCheckResult('openrouter', True, looks_valid, mask_secret(key), note)


def check_gemini_key(value: str | None) -> ApiKeyCheckResult:
    key = (value or '').strip()
    if not key:
        return ApiKeyCheckResult('gemini', False, False, '', 'Missing GEMINI_API_KEY')

    looks_valid = bool(re.fullmatch(r'AIza[0-9A-Za-z_\-]{20,}', key))
    note = 'Format looks valid' if looks_valid else 'Unexpected Gemini key format'
    return ApiKeyCheckResult('gemini', True, looks_valid, mask_secret(key), note)


def check_google_oauth_secret(value: str | None) -> ApiKeyCheckResult:
    key = (value or '').strip()
    if not key:
        return ApiKeyCheckResult('google_oauth_secret', False, False, '', 'Missing GOOGLE_OAUTH_CLIENT_SECRET')

    looks_valid = bool(re.fullmatch(r'GOCSPX-[0-9A-Za-z_\-]{10,}', key))
    note = 'Format looks valid' if looks_valid else 'Unexpected Google OAuth secret format'
    return ApiKeyCheckResult('google_oauth_secret', True, looks_valid, mask_secret(key), note)

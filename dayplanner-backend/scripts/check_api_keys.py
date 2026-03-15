import sys
from pathlib import Path

from dotenv import dotenv_values

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.api_key_checks import check_gemini_key, check_google_oauth_secret, check_openrouter_key


def main() -> None:
    env = dotenv_values('.env')

    results = [
        check_openrouter_key(env.get('OPENROUTER_API_KEY')),
        check_gemini_key(env.get('GEMINI_API_KEY')),
        check_google_oauth_secret(env.get('GOOGLE_OAUTH_CLIENT_SECRET')),
    ]

    print('API key format checks:')
    for result in results:
        status = 'OK' if result.looks_valid else 'WARN'
        presence = 'present' if result.present else 'missing'
        print(f"- {result.provider}: {status} ({presence}) value={result.masked_value} note={result.note}")


if __name__ == '__main__':
    main()

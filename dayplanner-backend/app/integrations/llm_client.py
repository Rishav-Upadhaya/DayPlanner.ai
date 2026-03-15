import httpx


def _extract_text_from_llm_response(response) -> str:
    content = getattr(response, 'content', '')
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get('text')
                if isinstance(text, str):
                    parts.append(text)
        return '\n'.join([part for part in parts if part]).strip()
    return str(content).strip()


class OpenRouterClient:
    def generate_text(self, api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model=model,
                api_key=api_key,
                base_url='https://openrouter.ai/api/v1',
                default_headers={
                    'HTTP-Referer': 'https://dayplanner.local',
                    'X-Title': 'DayPlanner Backend',
                },
                temperature=0.3,
                max_tokens=900,
                timeout=25,
            )
            response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
            text = _extract_text_from_llm_response(response)
            if text:
                return text
        except Exception:
            pass

        response = httpx.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://dayplanner.local',
                'X-Title': 'DayPlanner Backend',
            },
            json={
                'model': model,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                'temperature': 0.3,
                'max_tokens': 900,
            },
            timeout=25,
        )
        response.raise_for_status()
        payload = response.json()
        return payload['choices'][0]['message']['content'].strip()

    def generate_plan_summary(self, api_key: str, model: str, user_input: str, memory_snippets: list[str], plan_date: str) -> str:
        prompt = (
            'You are an expert daily planning assistant. '
            f'Create a concise 1-2 sentence summary for a daily plan on {plan_date}. '
            f'User input: {user_input}. '
            f'Memory context: {memory_snippets}.'
        )
        return self.generate_text(
            api_key=api_key,
            model=model,
            system_prompt='You create clear, actionable daily planning summaries.',
            user_prompt=prompt,
        )


class GeminiFallbackClient:
    def generate_text(self, api_key: str, model: str, system_prompt: str, user_prompt: str) -> str:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_google_genai import ChatGoogleGenerativeAI

            llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
                temperature=0.3,
                max_output_tokens=900,
                timeout=25,
            )
            response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
            text = _extract_text_from_llm_response(response)
            if text:
                return text
        except Exception:
            pass

        response = httpx.post(
            f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
            params={'key': api_key},
            headers={'Content-Type': 'application/json'},
            json={
                'contents': [
                    {
                        'parts': [
                            {
                                'text': f'{system_prompt}\n\n{user_prompt}',
                            }
                        ]
                    }
                ],
                'generationConfig': {
                    'temperature': 0.3,
                    'maxOutputTokens': 900,
                },
            },
            timeout=25,
        )
        response.raise_for_status()
        payload = response.json()
        candidates = payload.get('candidates', [])
        if not candidates:
            raise ValueError('Gemini response did not include candidates')
        parts = candidates[0].get('content', {}).get('parts', [])
        if not parts:
            raise ValueError('Gemini response did not include content parts')
        return parts[0].get('text', '').strip()

    def generate_plan_summary(self, api_key: str, model: str, user_input: str, memory_snippets: list[str], plan_date: str) -> str:
        prompt = (
            'You are an expert daily planning assistant. '
            f'Create a concise 1-2 sentence summary for a daily plan on {plan_date}. '
            f'User input: {user_input}. '
            f'Memory context: {memory_snippets}.'
        )
        return self.generate_text(
            api_key=api_key,
            model=model,
            system_prompt='You create clear, actionable daily planning summaries.',
            user_prompt=prompt,
        )


class AgentLLMGateway:
    def __init__(self) -> None:
        self.openrouter = OpenRouterClient()
        self.gemini = GeminiFallbackClient()

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        primary_provider: str,
        primary_api_key: str,
        primary_model: str,
        fallback_provider: str,
        fallback_api_key: str,
        fallback_model: str,
    ) -> str:
        provider_clients = {
            'openrouter': self.openrouter,
            'gemini': self.gemini,
        }

        primary = provider_clients.get((primary_provider or '').strip().lower())
        fallback = provider_clients.get((fallback_provider or '').strip().lower())

        try:
            if primary and primary_api_key and primary_model:
                return primary.generate_text(
                    api_key=primary_api_key,
                    model=primary_model,
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
        except Exception:
            pass

        if fallback and fallback_api_key and fallback_model:
            return fallback.generate_text(
                api_key=fallback_api_key,
                model=fallback_model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )

        raise ValueError('No configured LLM provider available for agent generation')


def list_openrouter_models(api_key: str) -> list[dict[str, str]]:
    response = httpx.get(
        'https://openrouter.ai/api/v1/models',
        headers={
            'Authorization': f'Bearer {api_key}',
            'HTTP-Referer': 'https://dayplanner.local',
            'X-Title': 'DayPlanner Backend',
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    rows = payload.get('data', [])
    return [{'id': item.get('id', ''), 'name': item.get('name', item.get('id', ''))} for item in rows if item.get('id')]


def list_gemini_models(api_key: str) -> list[dict[str, str]]:
    response = httpx.get(
        'https://generativelanguage.googleapis.com/v1beta/models',
        params={'key': api_key},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    rows = payload.get('models', [])
    return [{'id': item.get('name', '').replace('models/', ''), 'name': item.get('displayName', item.get('name', ''))} for item in rows if item.get('name')]


def get_openrouter_usage_pct(api_key: str) -> float:
    response = httpx.get(
        'https://openrouter.ai/api/v1/auth/key',
        headers={
            'Authorization': f'Bearer {api_key}',
            'HTTP-Referer': 'https://dayplanner.local',
            'X-Title': 'DayPlanner Backend',
        },
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json().get('data', {})
    usage = float(payload.get('usage', 0) or 0)
    limit = float(payload.get('limit', 0) or 0)
    if limit <= 0:
        return 0.0
    return (usage / limit) * 100

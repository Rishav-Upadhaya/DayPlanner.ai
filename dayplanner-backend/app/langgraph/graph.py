import re
from datetime import datetime

from app.core.config import get_settings
from app.integrations.llm_client import GeminiFallbackClient, OpenRouterClient
from app.schemas.plan import PlanBlockDTO
from app.services.graphrag import GraphRAGService


class PlanningGraph:
    CONTINUE_HINTS = ('continue yesterday', 'continue yesterday schedule', 'same as yesterday', 'carry forward')

    @staticmethod
    def _parse_hhmm_to_minutes(value: str) -> int:
        hours, minutes = value.split(':')
        return int(hours) * 60 + int(minutes)

    @staticmethod
    def _minutes_to_hhmm(value: int) -> str:
        value = max(0, value)
        hours = value // 60
        minutes = value % 60
        return f'{hours:02d}:{minutes:02d}'

    @staticmethod
    def _normalize_ampm_time(token: str) -> str | None:
        try:
            dt = datetime.strptime(token.strip().lower(), '%I:%M %p')
            return dt.strftime('%H:%M')
        except ValueError:
            return None

    @classmethod
    def _extract_class_window(cls, user_input: str) -> tuple[str, str] | None:
        pattern = re.search(r'from\s+(\d{1,2}:\d{2}\s*(?:am|pm))\s+to\s+(\d{1,2}:\d{2}\s*(?:am|pm))', user_input, re.IGNORECASE)
        if not pattern:
            return None
        start = cls._normalize_ampm_time(pattern.group(1))
        end = cls._normalize_ampm_time(pattern.group(2))
        if not start or not end:
            return None
        return start, end

    @staticmethod
    def _extract_tasks(user_input: str) -> list[str]:
        normalized = re.sub(r'\band\b', ',', user_input, flags=re.IGNORECASE)
        normalized = re.sub(r'\s+', ' ', normalized)
        raw_chunks = [chunk.strip(' .,!') for chunk in normalized.split(',')]
        return [chunk for chunk in raw_chunks if chunk][:8]

    @staticmethod
    def _detect_repeat_days(user_input: str) -> int | None:
        match = re.search(r'for\s+(\d+)\s+days', user_input, re.IGNORECASE)
        if not match:
            return None
        try:
            days = int(match.group(1))
            return max(1, min(14, days))
        except ValueError:
            return None

    @classmethod
    def _generate_blocks_from_input(
        cls,
        user_input: str,
        *,
        previous_day_blocks: list[dict] | None = None,
    ) -> list[PlanBlockDTO]:
        lowered_input = user_input.lower()

        if previous_day_blocks and any(hint in lowered_input for hint in cls.CONTINUE_HINTS):
            reused_blocks: list[PlanBlockDTO] = []
            for block in previous_day_blocks:
                reused_blocks.append(
                    PlanBlockDTO(
                        title=block.get('title', 'Carry-forward task'),
                        start_time=block.get('start_time', '09:00'),
                        end_time=block.get('end_time', '10:00'),
                        priority=block.get('priority', 'medium'),
                        category=block.get('category', 'work'),
                        completed=False,
                    )
                )
            if reused_blocks:
                return reused_blocks

        keywords_to_category = {
            'meeting': 'meeting',
            'call': 'meeting',
            'gym': 'health',
            'workout': 'health',
            'class': 'class',
            'study': 'class',
            'lunch': 'break',
            'break': 'break',
        }

        class_window = cls._extract_class_window(user_input)
        extracted_tasks = cls._extract_tasks(user_input)

        generated: list[PlanBlockDTO] = []
        start_minutes = 9 * 60

        if class_window:
            class_start, class_end = class_window
            generated.append(
                PlanBlockDTO(
                    title='Class schedule',
                    start_time=class_start,
                    end_time=class_end,
                    priority='high',
                    category='class',
                    completed=False,
                )
            )
            start_minutes = cls._parse_hhmm_to_minutes(class_end) + 30
            generated.append(
                PlanBlockDTO(
                    title='Recovery break after class',
                    start_time=cls._minutes_to_hhmm(start_minutes),
                    end_time=cls._minutes_to_hhmm(start_minutes + 30),
                    priority='low',
                    category='break',
                    completed=False,
                )
            )
            start_minutes += 45

        for index, chunk in enumerate(extracted_tasks[:6]):
            lowered = chunk.lower()
            category = 'work'
            priority = 'medium'
            for key, value in keywords_to_category.items():
                if key in lowered:
                    category = value
                    break
            if any(token in lowered for token in ['urgent', 'important', 'deadline', 'deep work']):
                priority = 'high'

            block_start = start_minutes + (index * 75)
            block_end = block_start + 60
            generated.append(
                PlanBlockDTO(
                    title=chunk[:120],
                    start_time=cls._minutes_to_hhmm(block_start),
                    end_time=cls._minutes_to_hhmm(block_end),
                    priority=priority,
                    category=category,
                    completed=False,
                )
            )

        repeat_days = cls._detect_repeat_days(user_input)
        if repeat_days and generated:
            generated.append(
                PlanBlockDTO(
                    title=f'Repeat-cycle checkpoint (day 1 of {repeat_days})',
                    start_time=cls._minutes_to_hhmm(start_minutes + len(generated) * 75),
                    end_time=cls._minutes_to_hhmm(start_minutes + len(generated) * 75 + 30),
                    priority='medium',
                    category='work',
                    completed=False,
                )
            )

        if generated:
            return generated

        return [
            PlanBlockDTO(title='Morning focus session', start_time='09:00', end_time='10:00', priority='high', category='work', completed=False),
            PlanBlockDTO(title='Execution block', start_time='10:15', end_time='11:15', priority='medium', category='work', completed=False),
            PlanBlockDTO(title='Recovery break', start_time='11:30', end_time='12:00', priority='low', category='break', completed=False),
        ]

    def __init__(self) -> None:
        self.memory = GraphRAGService()
        self.openrouter = OpenRouterClient()
        self.gemini = GeminiFallbackClient()

    def _generate_summary(
        self,
        *,
        user_input: str,
        plan_date: str,
        memory_snippets: list[str],
        primary_provider: str,
        primary_api_key: str,
        primary_model: str,
        fallback_provider: str,
        fallback_api_key: str,
        fallback_model: str,
        previous_day_summary: str | None,
    ) -> str:
        first_snippet = memory_snippets[0] if memory_snippets else ''
        compact_input = ' '.join(user_input.strip().split())
        compact_input = compact_input[:180]
        carry_forward_hint = f' Carry-forward: {previous_day_summary}.' if previous_day_summary else ''
        default_summary = (
            f'Planned for {plan_date}: {compact_input}. '
            + (f'Context used: {first_snippet}.' if first_snippet else 'Generated from your latest request.')
            + carry_forward_hint
        )

        provider_map = {
            'openrouter': (self.openrouter, primary_api_key, primary_model),
            'gemini': (self.gemini, primary_api_key, primary_model),
        }
        fallback_map = {
            'openrouter': (self.openrouter, fallback_api_key, fallback_model),
            'gemini': (self.gemini, fallback_api_key, fallback_model),
        }

        primary_provider = (primary_provider or '').strip().lower()
        fallback_provider = (fallback_provider or '').strip().lower()

        try:
            client, api_key, model = provider_map.get(primary_provider, (None, '', ''))
            if client and api_key and model:
                return client.generate_plan_summary(
                    api_key=api_key,
                    model=model,
                    user_input=user_input,
                    memory_snippets=memory_snippets,
                    plan_date=plan_date,
                )
        except Exception:
            pass

        try:
            client, api_key, model = fallback_map.get(fallback_provider, (None, '', ''))
            if client and api_key and model:
                return client.generate_plan_summary(
                    api_key=api_key,
                    model=model,
                    user_input=user_input,
                    memory_snippets=memory_snippets,
                    plan_date=plan_date,
                )
        except Exception:
            pass

        return default_summary

    def run(
        self,
        user_id: str,
        user_input: str,
        plan_date: str,
        *,
        primary_provider: str | None = None,
        primary_api_key: str | None = None,
        primary_model: str | None = None,
        fallback_provider: str | None = None,
        fallback_api_key: str | None = None,
        fallback_model: str | None = None,
        previous_day_blocks: list[dict] | None = None,
        previous_day_summary: str | None = None,
    ) -> dict:
        settings = get_settings()
        memory = self.memory.retrieve_user_context(user_id=user_id, query=user_input)

        chosen_primary_provider = primary_provider or ('openrouter' if settings.openrouter_api_key else 'gemini')
        chosen_primary_api_key = primary_api_key or (
            settings.openrouter_api_key if chosen_primary_provider == 'openrouter' else settings.gemini_api_key
        )
        chosen_primary_model = primary_model or (
            settings.openrouter_model if chosen_primary_provider == 'openrouter' else settings.gemini_model
        )

        chosen_fallback_provider = fallback_provider or ('gemini' if chosen_primary_provider == 'openrouter' else 'openrouter')
        chosen_fallback_api_key = fallback_api_key or (
            settings.gemini_api_key if chosen_fallback_provider == 'gemini' else settings.openrouter_api_key
        )
        chosen_fallback_model = fallback_model or (
            settings.gemini_model if chosen_fallback_provider == 'gemini' else settings.openrouter_model
        )

        summary = self._generate_summary(
            user_input=user_input,
            plan_date=plan_date,
            memory_snippets=memory.snippets,
            primary_provider=chosen_primary_provider,
            primary_api_key=chosen_primary_api_key,
            primary_model=chosen_primary_model,
            fallback_provider=chosen_fallback_provider,
            fallback_api_key=chosen_fallback_api_key,
            fallback_model=chosen_fallback_model,
            previous_day_summary=previous_day_summary,
        )
        blocks = self._generate_blocks_from_input(user_input=user_input, previous_day_blocks=previous_day_blocks)

        if any(hint in user_input.lower() for hint in self.CONTINUE_HINTS) and previous_day_summary:
            summary = (
                f'Continuing your previous plan on {plan_date}. '
                f'{previous_day_summary} I carried forward your open priorities and added a focused sequence for today.'
            )

        return {
            'summary': summary,
            'memory_snippets': memory.snippets,
            'blocks': [block.model_dump() for block in blocks],
        }

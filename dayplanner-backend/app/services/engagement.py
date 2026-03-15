from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.integrations.llm_client import AgentLLMGateway
from app.repositories.engagement import EngagementRepository
from app.repositories.llm import LLMRepository
from app.repositories.plans import PlanRepository
from app.services.graphrag import GraphRAGService


class EngagementPromptService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = EngagementRepository(db)

    def run_once(self, now_utc: datetime | None = None) -> None:
        current_utc = now_utc or datetime.now(timezone.utc)
        users = self.repository.list_active_users_with_settings()

        has_changes = False
        for user, setting in users:
            timezone_name = (setting.timezone if setting else 'UTC') or 'UTC'
            tzinfo = self._resolve_timezone(timezone_name)
            local_now = current_utc.astimezone(tzinfo)

            local_date = local_now.date().isoformat()
            local_minutes = local_now.hour * 60 + local_now.minute
            morning_minutes = self._parse_hhmm_to_minutes(setting.morning_briefing_time if setting else None, fallback='07:30')
            evening_minutes = self._parse_hhmm_to_minutes(setting.evening_checkin_time if setting else None, fallback='20:00')

            state = self.repository.get_state(user.id)
            last_morning_date = state.last_morning_prompt_date if state else None
            last_evening_date = state.last_evening_prompt_date if state else None

            in_morning_window = local_minutes >= morning_minutes and (
                evening_minutes <= morning_minutes or local_minutes < evening_minutes
            )
            should_send_morning = in_morning_window and last_morning_date != local_date
            should_send_evening = local_minutes >= evening_minutes and last_evening_date != local_date

            if (should_send_morning or should_send_evening) and state is None:
                state = self.repository.create_state(user.id)

            weekday = local_now.strftime('%A')
            if should_send_morning and state is not None:
                morning_message = self._generate_morning_message(
                    user_id=user.id,
                    weekday=weekday,
                    local_date=local_date,
                )
                self.repository.create_notification(
                    user_id=user.id,
                    kind='engagement',
                    message=morning_message,
                )
                state.last_morning_prompt_date = local_date
                has_changes = True

            if should_send_evening and state is not None:
                self.repository.create_notification(
                    user_id=user.id,
                    kind='engagement',
                    message='Evening check-in time. Share a quick reflection in chat so tomorrow\'s plan gets smarter.',
                )
                state.last_evening_prompt_date = local_date
                has_changes = True

            if should_send_morning or should_send_evening:
                state.updated_at = datetime.utcnow()

        if has_changes:
            self.repository.commit()

    def _resolve_timezone(self, timezone_name: str):
        try:
            return ZoneInfo(timezone_name)
        except Exception:
            return timezone.utc

    def _parse_hhmm_to_minutes(self, value: str | None, fallback: str) -> int:
        raw = (value or fallback).strip()
        parts = raw.split(':')
        if len(parts) != 2:
            parts = fallback.split(':')

        try:
            hour = int(parts[0])
            minute = int(parts[1])
        except Exception:
            hour, minute = [int(part) for part in fallback.split(':')]

        hour = max(0, min(23, hour))
        minute = max(0, min(59, minute))
        return hour * 60 + minute

    def _generate_morning_message(self, user_id: str, weekday: str, local_date: str) -> str:
        try:
            llm_config = LLMRepository(self.db).get_or_create_config(user_id=user_id)
            if not llm_config.primary_api_key or not llm_config.primary_model:
                raise ValueError('No LLM configured')

            from datetime import date, timedelta

            yesterday = (date.fromisoformat(local_date) - timedelta(days=1)).isoformat()
            yesterday_plan = PlanRepository(self.db).get_by_day_iso(user_id=user_id, day_iso=yesterday)

            completion_context = ''
            if yesterday_plan and yesterday_plan.blocks:
                completed = sum(1 for block in yesterday_plan.blocks if block.completed)
                total = len(yesterday_plan.blocks)
                completion_context = f'Yesterday ({yesterday}): completed {completed}/{total} tasks.'

            memory = GraphRAGService().retrieve_user_context(
                user_id=user_id,
                query='morning planning priorities goals',
            )
            memory_context = ' | '.join(memory.snippets[:3]) if memory.snippets else ''

            system_prompt = (
                'You are a friendly, energizing daily planning assistant. '
                'Generate a SHORT (2-3 sentences) personalized morning briefing. '
                'Be warm, motivating, and specific. Mention yesterday if available. '
                'End with one actionable suggestion for today.'
            )
            user_prompt = (
                f"User's morning — {weekday}, {local_date}.\n"
                f'{completion_context}\n'
                f'User preferences/patterns: {memory_context}\n'
                'Generate a brief, personalized morning briefing.'
            )

            gateway = AgentLLMGateway()
            generated = gateway.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                primary_provider=llm_config.primary_provider,
                primary_api_key=llm_config.primary_api_key,
                primary_model=llm_config.primary_model,
                fallback_provider=llm_config.fallback_provider,
                fallback_api_key=llm_config.fallback_api_key,
                fallback_model=llm_config.fallback_model,
            )
            return generated.strip() or (
                f'Good morning! Ready to make the most of your {weekday}? '
                "Open chat and share today's priorities."
            )
        except Exception:
            return (
                f'Good morning! Ready to make the most of your {weekday}? '
                "Open chat and share today's priorities."
            )

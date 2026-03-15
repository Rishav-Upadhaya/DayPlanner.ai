from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.repositories.engagement import EngagementRepository


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
                self.repository.create_notification(
                    user_id=user.id,
                    kind='engagement',
                    message=f'Good morning! Ready to plan your {weekday}? Open chat and share today\'s priorities.',
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

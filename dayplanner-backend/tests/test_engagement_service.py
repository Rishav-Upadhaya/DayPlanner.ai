from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.engagement import UserEngagementState
from app.models.llm import UserNotification
from app.models.user import User, UserSetting
from app.services.engagement import EngagementPromptService


def _create_user_with_settings(db, tz: str = 'UTC', morning: str = '07:30', evening: str = '20:00') -> str:
    user = User(
        email=f"engagement-{uuid4().hex[:12]}@example.com",
        full_name='Engagement Test',
        password_hash='hashed',
        is_active=True,
    )
    db.add(user)
    db.flush()

    setting = UserSetting(
        user_id=user.id,
        timezone=tz,
        planning_style='balanced',
        morning_briefing_time=morning,
        evening_checkin_time=evening,
    )
    db.add(setting)
    db.commit()
    return user.id


def test_morning_prompt_sent_once_per_day() -> None:
    db = SessionLocal()
    try:
        user_id = _create_user_with_settings(db)
        service = EngagementPromptService(db)

        service.run_once(now_utc=datetime(2026, 3, 15, 8, 0, tzinfo=timezone.utc))
        service.run_once(now_utc=datetime(2026, 3, 15, 8, 15, tzinfo=timezone.utc))

        notifications = list(db.scalars(select(UserNotification).where(UserNotification.user_id == user_id)).all())
        state = db.scalar(select(UserEngagementState).where(UserEngagementState.user_id == user_id))

        morning_notifications = [item for item in notifications if 'Good morning' in item.message]
        assert len(morning_notifications) == 1
        assert state is not None
        assert state.last_morning_prompt_date == '2026-03-15'
    finally:
        db.close()


def test_evening_prompt_sent_after_evening_time() -> None:
    db = SessionLocal()
    try:
        user_id = _create_user_with_settings(db)
        service = EngagementPromptService(db)

        service.run_once(now_utc=datetime(2026, 3, 15, 21, 0, tzinfo=timezone.utc))

        notifications = list(db.scalars(select(UserNotification).where(UserNotification.user_id == user_id)).all())
        state = db.scalar(select(UserEngagementState).where(UserEngagementState.user_id == user_id))

        assert any('Evening check-in time' in item.message for item in notifications)
        assert state is not None
        assert state.last_evening_prompt_date == '2026-03-15'
    finally:
        db.close()


def test_timezone_aware_morning_prompt() -> None:
    db = SessionLocal()
    try:
        user_id = _create_user_with_settings(db, tz='Asia/Kolkata', morning='07:30', evening='20:00')
        service = EngagementPromptService(db)

        service.run_once(now_utc=datetime(2026, 3, 15, 2, 35, tzinfo=timezone.utc))

        notifications = list(db.scalars(select(UserNotification).where(UserNotification.user_id == user_id)).all())
        assert any('Good morning' in item.message for item in notifications)
    finally:
        db.close()

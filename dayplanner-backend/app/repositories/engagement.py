from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.engagement import UserEngagementState
from app.models.llm import UserNotification
from app.models.user import User, UserSetting


class EngagementRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_active_users_with_settings(self) -> list[tuple[User, UserSetting | None]]:
        stmt = (
            select(User, UserSetting)
            .outerjoin(UserSetting, UserSetting.user_id == User.id)
            .where(User.is_active.is_(True))
        )
        return list(self.db.execute(stmt).all())

    def get_state(self, user_id: str) -> UserEngagementState | None:
        stmt = select(UserEngagementState).where(UserEngagementState.user_id == user_id)
        return self.db.scalar(stmt)

    def create_state(self, user_id: str) -> UserEngagementState:
        state = UserEngagementState(user_id=user_id)
        self.db.add(state)
        self.db.flush()
        return state

    def create_notification(self, user_id: str, kind: str, message: str) -> UserNotification:
        notification = UserNotification(user_id=user_id, kind=kind, message=message)
        self.db.add(notification)
        self.db.flush()
        return notification

    def commit(self) -> None:
        self.db.commit()

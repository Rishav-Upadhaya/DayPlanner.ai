from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.llm import UserLLMConfig, UserNotification


class LLMRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_config(self, user_id: str) -> UserLLMConfig:
        stmt = select(UserLLMConfig).where(UserLLMConfig.user_id == user_id)
        config = self.db.scalar(stmt)
        if config:
            return config

        config = UserLLMConfig(user_id=user_id)
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update_config(self, config: UserLLMConfig, data: dict) -> UserLLMConfig:
        for key, value in data.items():
            if value is not None and hasattr(config, key):
                setattr(config, key, value)
        config.updated_at = datetime.utcnow()
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def create_notification(self, user_id: str, kind: str, message: str) -> UserNotification:
        notification = UserNotification(user_id=user_id, kind=kind, message=message)
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def list_notifications(self, user_id: str) -> list[UserNotification]:
        stmt = (
            select(UserNotification)
            .where(UserNotification.user_id == user_id)
            .order_by(UserNotification.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

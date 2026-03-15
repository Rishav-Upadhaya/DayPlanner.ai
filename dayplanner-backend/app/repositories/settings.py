from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import UserSetting


class SettingsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create(self, user_id: str) -> UserSetting:
        stmt = select(UserSetting).where(UserSetting.user_id == user_id)
        setting = self.db.scalar(stmt)
        if setting:
            return setting

        setting = UserSetting(user_id=user_id)
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting

    def update(self, setting: UserSetting, data: dict) -> UserSetting:
        for key, value in data.items():
            if value is not None and hasattr(setting, key):
                setattr(setting, key, value)
        self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting

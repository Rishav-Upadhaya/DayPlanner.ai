from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = 'users'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default='')
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    google_sub: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    settings: Mapped['UserSetting'] = relationship(back_populates='user', uselist=False)


class UserSetting(Base):
    __tablename__ = 'user_settings'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'), unique=True)
    timezone: Mapped[str] = mapped_column(String(64), default='UTC')
    planning_style: Mapped[str] = mapped_column(String(32), default='balanced')
    morning_briefing_time: Mapped[str] = mapped_column(String(5), default='07:30')
    evening_checkin_time: Mapped[str] = mapped_column(String(5), default='20:00')

    user: Mapped[User] = relationship(back_populates='settings')

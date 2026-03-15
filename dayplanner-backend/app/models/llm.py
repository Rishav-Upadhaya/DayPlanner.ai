from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserLLMConfig(Base):
    __tablename__ = 'user_llm_configs'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'), unique=True, index=True)
    primary_provider: Mapped[str] = mapped_column(String(32), default='openrouter')
    primary_api_key: Mapped[str] = mapped_column(Text, default='')
    primary_model: Mapped[str] = mapped_column(String(128), default='')
    fallback_provider: Mapped[str] = mapped_column(String(32), default='gemini')
    fallback_api_key: Mapped[str] = mapped_column(Text, default='')
    fallback_model: Mapped[str] = mapped_column(String(128), default='')
    usage_alert_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    usage_alert_threshold_pct: Mapped[int] = mapped_column(Integer, default=85)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserNotification(Base):
    __tablename__ = 'user_notifications'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'), index=True)
    kind: Mapped[str] = mapped_column(String(64), default='info')
    message: Mapped[str] = mapped_column(Text)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

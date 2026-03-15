from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AnalyticsSnapshot(Base):
    __tablename__ = 'analytics_snapshots'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'), index=True)
    period: Mapped[str] = mapped_column(String(16), default='7d')
    completion_rate: Mapped[float] = mapped_column(Float, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    memory_patterns_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

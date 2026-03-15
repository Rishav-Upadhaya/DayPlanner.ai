from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.planning import Plan, PlanBlock


class HistoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def summary(self, user_id: str, days: int = 7) -> dict:
        start_day = date.today() - timedelta(days=days - 1)

        total_stmt = (
            select(func.count(PlanBlock.id))
            .join(Plan, Plan.id == PlanBlock.plan_id)
            .where(Plan.user_id == user_id, Plan.day >= start_day)
        )
        completed_stmt = (
            select(func.count(PlanBlock.id))
            .join(Plan, Plan.id == PlanBlock.plan_id)
            .where(Plan.user_id == user_id, Plan.day >= start_day, PlanBlock.completed.is_(True))
        )

        total_blocks = int(self.db.scalar(total_stmt) or 0)
        completed_blocks = int(self.db.scalar(completed_stmt) or 0)

        completion_rate = (completed_blocks / total_blocks * 100) if total_blocks else 0.0

        days_with_completion = (
            select(Plan.day)
            .join(PlanBlock, PlanBlock.plan_id == Plan.id)
            .where(Plan.user_id == user_id, PlanBlock.completed.is_(True))
            .group_by(Plan.day)
            .order_by(Plan.day.desc())
        )
        completed_days = [row for row in self.db.scalars(days_with_completion).all()]

        streak = 0
        cursor = date.today()
        completed_set = set(completed_days)
        while cursor in completed_set:
            streak += 1
            cursor -= timedelta(days=1)

        return {
            'completion_rate': round(completion_rate, 1),
            'streak_days': streak,
            'memory_patterns_count': max(3, min(120, total_blocks + 5)),
        }

    def weekly_performance(self, user_id: str) -> list[dict]:
        labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        today = date.today()
        start = today - timedelta(days=today.weekday())

        rows = []
        for offset in range(7):
            target_day = start + timedelta(days=offset)

            total_stmt = (
                select(func.count(PlanBlock.id))
                .join(Plan, Plan.id == PlanBlock.plan_id)
                .where(Plan.user_id == user_id, Plan.day == target_day)
            )
            completed_stmt = (
                select(func.count(PlanBlock.id))
                .join(Plan, Plan.id == PlanBlock.plan_id)
                .where(Plan.user_id == user_id, Plan.day == target_day, PlanBlock.completed.is_(True))
            )

            total = int(self.db.scalar(total_stmt) or 0)
            completed = int(self.db.scalar(completed_stmt) or 0)
            score = int(round((completed / total) * 100)) if total else 0
            rows.append({'day': labels[offset], 'completion': score})

        return rows

    def archived_plans(self, user_id: str, limit: int = 10) -> list[dict]:
        stmt = select(Plan).where(Plan.user_id == user_id).order_by(Plan.day.desc()).limit(limit)
        plans = list(self.db.scalars(stmt).all())
        rows = []

        for plan in plans:
            total = len(plan.blocks)
            done = len([block for block in plan.blocks if block.completed])
            completion = int(round((done / total) * 100)) if total else 0
            rows.append(
                {
                    'id': plan.id,
                    'date': plan.day.isoformat(),
                    'tasks_planned': total,
                    'completion_rate': completion,
                    'status': 'archived',
                }
            )

        return rows

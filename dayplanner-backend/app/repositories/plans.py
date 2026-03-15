from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.planning import Plan, PlanBlock


class PlanRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_day(self, user_id: str, day: date) -> Plan | None:
        stmt = select(Plan).where(Plan.user_id == user_id, Plan.day == day)
        return self.db.scalar(stmt)

    def get_by_day_iso(self, user_id: str, day_iso: str) -> Plan | None:
        return self.get_by_day(user_id=user_id, day=date.fromisoformat(day_iso))

    def create_plan(self, user_id: str, day: date, summary: str, blocks: list[dict]) -> Plan:
        plan = Plan(user_id=user_id, day=day, summary=summary)
        self.db.add(plan)
        self.db.flush()

        for index, block in enumerate(blocks):
            self.db.add(
                PlanBlock(
                    plan_id=plan.id,
                    title=block.get('title', ''),
                    start_time=block.get('start_time', '09:00'),
                    end_time=block.get('end_time', '09:30'),
                    priority=block.get('priority', 'medium'),
                    category=block.get('category', 'work'),
                    completed=bool(block.get('completed', False)),
                    order_index=index,
                )
            )

        self.db.commit()
        self.db.refresh(plan)
        return plan

    def upsert_plan_for_day(self, user_id: str, day: date, summary: str, blocks: list[dict]) -> Plan:
        existing = self.get_by_day(user_id=user_id, day=day)
        if not existing:
            return self.create_plan(user_id=user_id, day=day, summary=summary, blocks=blocks)

        existing.summary = summary
        self.db.add(existing)
        self.db.flush()

        self.db.execute(delete(PlanBlock).where(PlanBlock.plan_id == existing.id))
        self.db.flush()

        for index, block in enumerate(blocks):
            self.db.add(
                PlanBlock(
                    plan_id=existing.id,
                    title=block.get('title', ''),
                    start_time=block.get('start_time', '09:00'),
                    end_time=block.get('end_time', '09:30'),
                    priority=block.get('priority', 'medium'),
                    category=block.get('category', 'work'),
                    completed=bool(block.get('completed', False)),
                    order_index=index,
                )
            )

        self.db.commit()
        self.db.refresh(existing)
        return existing

    def set_block_completion(self, plan_id: str, block_id: str, completed: bool) -> PlanBlock | None:
        stmt = select(PlanBlock).where(PlanBlock.plan_id == plan_id, PlanBlock.id == block_id)
        block = self.db.scalar(stmt)
        if not block:
            return None
        block.completed = completed
        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)
        return block

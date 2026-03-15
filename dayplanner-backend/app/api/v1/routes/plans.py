from datetime import date as DateType

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user_id
from app.core.database import get_db
from app.langgraph.graph import PlanningGraph
from app.models.planning import Plan
from app.repositories.memory import MemoryRepository
from app.repositories.plans import PlanRepository
from app.schemas.plan import GeneratePlanRequest, PlanDTO, PlanBlockDTO

router = APIRouter()
planning_graph = PlanningGraph()


def _to_plan_dto(plan) -> PlanDTO:
    blocks = [
        PlanBlockDTO(
            id=block.id,
            title=block.title,
            start_time=block.start_time,
            end_time=block.end_time,
            priority=block.priority,
            category=block.category,
            completed=block.completed,
        )
        for block in sorted(plan.blocks, key=lambda item: item.order_index)
    ]
    return PlanDTO(id=plan.id, date=plan.day.isoformat(), summary=plan.summary, blocks=blocks)


@router.get('/today', response_model=PlanDTO)
def get_today_plan(
    plan_date: str = Query(alias='date'),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> PlanDTO:
    repository = PlanRepository(db)
    target_day = DateType.fromisoformat(plan_date)
    existing = repository.get_by_day(user_id=user_id, day=target_day)
    if existing:
        return _to_plan_dto(existing)

    generated = planning_graph.run(user_id=user_id, user_input='Generate today plan', plan_date=plan_date)
    created = repository.create_plan(
        user_id=user_id,
        day=target_day,
        summary=generated['summary'],
        blocks=generated['blocks'],
    )
    return _to_plan_dto(created)


@router.post('/generate', response_model=PlanDTO)
def generate_plan(
    payload: GeneratePlanRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> PlanDTO:
    repository = PlanRepository(db)
    target_day = DateType.fromisoformat(payload.date_for_plan)
    result = planning_graph.run(user_id=user_id, user_input=payload.user_input, plan_date=payload.date_for_plan)
    created = repository.upsert_plan_for_day(
        user_id=user_id,
        day=target_day,
        summary=result['summary'],
        blocks=result['blocks'],
    )
    return _to_plan_dto(created)


@router.patch('/{plan_id}/blocks/{block_id}')
def update_block(
    plan_id: str,
    block_id: str,
    completed: bool,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    repository = PlanRepository(db)
    block = repository.set_block_completion(plan_id=plan_id, block_id=block_id, completed=completed)
    if not block:
        raise HTTPException(status_code=404, detail='Plan block not found')
    return {'plan_id': plan_id, 'block_id': block_id, 'completed': block.completed, 'user_id': user_id}


@router.post('/{plan_id}/apply-suggestion')
def apply_suggestion(plan_id: str, user_id: str = Depends(get_current_user_id)) -> dict:
    return {'plan_id': plan_id, 'status': 'applied', 'user_id': user_id}


@router.post('/{plan_id}/evening-checkin')
def evening_checkin(plan_id: str, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> dict[str, str]:
    stmt = select(Plan).where(Plan.id == plan_id, Plan.user_id == user_id)
    plan = db.scalar(stmt)
    if not plan or plan.user_id != user_id:
        raise HTTPException(status_code=404, detail='Plan not found')

    total_blocks = len(plan.blocks)
    completed_blocks = len([block for block in plan.blocks if block.completed])
    completion_pct = int((completed_blocks / total_blocks) * 100) if total_blocks else 0
    message = (
        f'You completed {completed_blocks} of {total_blocks} tasks today ({completion_pct}%). '
        'Great work—tomorrow\'s plan will adapt from this progress.'
    )

    memory_repo = MemoryRepository(db)
    memory_note = (
        f'Evening check-in for {plan.day.isoformat()}: completed {completed_blocks}/{total_blocks} '
        f'blocks ({completion_pct}%).'
    )
    memory_repo.add_node(user_id=user_id, node_type='reflection', content=memory_note, confidence='high')

    return {
        'status': 'recorded',
        'plan_id': plan_id,
        'message': message,
        'completion_pct': str(completion_pct),
    }

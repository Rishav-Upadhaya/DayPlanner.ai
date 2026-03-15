from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user_id
from app.core.database import get_db
from app.repositories.history import HistoryRepository
from app.schemas.history import HistorySummaryDTO, WeeklyPointDTO

router = APIRouter()


@router.get('/summary', response_model=HistorySummaryDTO)
def history_summary(range: str = '7d', user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> HistorySummaryDTO:
    repository = HistoryRepository(db)
    days = 7 if range == '7d' else 30
    summary = repository.summary(user_id=user_id, days=days)
    return HistorySummaryDTO(**summary)


@router.get('/weekly-performance', response_model=list[WeeklyPointDTO])
def weekly_performance(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> list[WeeklyPointDTO]:
    repository = HistoryRepository(db)
    rows = repository.weekly_performance(user_id=user_id)
    return [WeeklyPointDTO(day=row['day'], completion=row['completion']) for row in rows]


@router.get('/plans')
def archived_plans(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> list[dict]:
    repository = HistoryRepository(db)
    return repository.archived_plans(user_id=user_id)

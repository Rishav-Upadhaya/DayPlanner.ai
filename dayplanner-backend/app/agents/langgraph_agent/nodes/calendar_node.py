import logging

from app.agents.langgraph_agent.state import AgentState
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.repositories.calendar import CalendarRepository
from app.services.calendar_sync import CalendarSyncService

logger = logging.getLogger(__name__)


class CalendarReaderNode:
    def run(self, state: AgentState) -> dict:
        existing_events = state.get('existing_calendar_events', [])
        user_id = state.get('user_id', '')
        if not user_id:
            return {'existing_calendar_events': existing_events}

        db = SessionLocal()
        try:
            plan_date = state.get('plan_date', '')

            service = CalendarSyncService(db=db, settings=get_settings())
            try:
                service.sync_user_for_day(user_id=user_id, day=plan_date)
            except Exception as exc:
                logger.warning('Calendar sync in agent failed: %s', exc)

            repo = CalendarRepository(db)
            try:
                events = repo.list_events_for_day(user_id=user_id, day=plan_date)
                return {
                    'existing_calendar_events': [
                        {
                            'id': event.external_id,
                            'title': event.title,
                            'date': plan_date,
                            'start_time': event.starts_at.strftime('%H:%M'),
                            'end_time': event.ends_at.strftime('%H:%M'),
                        }
                        for event in events
                    ]
                    or existing_events
                }
            except Exception:
                return {'existing_calendar_events': existing_events}
        finally:
            db.close()

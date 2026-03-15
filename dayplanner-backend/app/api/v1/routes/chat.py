from datetime import date
from datetime import timedelta
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agents.dayplanner_agent import DayPlannerAgent
from app.api.v1.deps import get_current_user_id
from app.core.config import get_settings
from app.core.database import get_db
from app.repositories.calendar import CalendarRepository
from app.repositories.chat import ChatRepository
from app.repositories.llm import LLMRepository
from app.repositories.plans import PlanRepository
from app.schemas.chat import ChatMessageCreate, ChatResponseDTO
from app.schemas.plan import PlanBlockDTO
from app.services.calendar_sync import CalendarSyncService
from app.services.graphrag import GraphRAGService

router = APIRouter()
dayplanner_agent = DayPlannerAgent()
memory_service = GraphRAGService()


def _serialize_day_events(day_events, target_day: date) -> list[dict[str, str]]:
    return [
        {
            'id': event.external_id,
            'title': event.title,
            'date': target_day.isoformat(),
            'start_time': event.starts_at.strftime('%H:%M'),
            'end_time': event.ends_at.strftime('%H:%M'),
        }
        for event in day_events
    ]


def _build_chat_context(db: Session, user_id: str, session_id: str, payload: ChatMessageCreate) -> dict:
    plan_repository = PlanRepository(db)
    llm_repository = LLMRepository(db)
    calendar_repository = CalendarRepository(db)
    settings = get_settings()

    target_day = date.today()
    if payload.plan_date:
        try:
            target_day = date.fromisoformat(payload.plan_date)
        except ValueError:
            target_day = date.today()

    llm_config = llm_repository.get_or_create_config(user_id=user_id)

    try:
        CalendarSyncService(db=db, settings=settings).sync_user_for_day(user_id=user_id, day=target_day.isoformat())
    except Exception:
        pass

    existing_calendar_events = []
    try:
        day_events = calendar_repository.list_events_for_day(user_id=user_id, day=target_day.isoformat())
        existing_calendar_events = _serialize_day_events(day_events=day_events, target_day=target_day)
    except Exception:
        existing_calendar_events = []

    memory = memory_service.retrieve_user_context(user_id=user_id, query=payload.content)
    preference_snippets = memory_service.retrieve_preference_context(user_id=user_id, limit=6)
    memory_snippets: list[str] = []
    seen: set[str] = set()
    for snippet in preference_snippets + memory.snippets:
        normalized = str(snippet).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        memory_snippets.append(normalized)
    chat_repository = ChatRepository(db)
    recent_messages = [
        {
            'role': message.role,
            'content': message.content,
        }
        for message in chat_repository.list_recent_messages(session_id=session_id, limit=16)
    ]

    previous_day = target_day - timedelta(days=1)
    previous_plan = plan_repository.get_by_day(user_id=user_id, day=previous_day)
    previous_day_summary = previous_plan.summary if previous_plan else ''
    previous_day_blocks = []
    if previous_plan:
        previous_day_blocks = [
            {
                'title': block.title,
                'start_time': block.start_time,
                'end_time': block.end_time,
                'priority': block.priority,
                'category': block.category,
                'completed': block.completed,
            }
            for block in sorted(previous_plan.blocks, key=lambda item: item.order_index)
        ]

    return {
        'target_day': target_day,
        'llm_config': {
            'primary_provider': llm_config.primary_provider,
            'primary_api_key': llm_config.primary_api_key,
            'primary_model': llm_config.primary_model,
            'fallback_provider': llm_config.fallback_provider,
            'fallback_api_key': llm_config.fallback_api_key,
            'fallback_model': llm_config.fallback_model,
        },
        'calendar_events': existing_calendar_events,
        'memory_snippets': memory_snippets[:12],
        'recent_messages': recent_messages,
        'previous_day_summary': previous_day_summary,
        'previous_day_blocks': previous_day_blocks,
    }


@router.post('/sessions')
def create_session(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> dict[str, str]:
    repository = ChatRepository(db)
    session = repository.create_session(user_id=user_id, title='Planning Session')
    return {'session_id': session.id, 'status': 'created'}


@router.get('/sessions')
def list_sessions(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> list[dict[str, str]]:
    repository = ChatRepository(db)
    sessions = repository.list_sessions(user_id=user_id)
    return [
        {
            'id': item.id,
            'title': item.title,
            'created_at': item.created_at.isoformat(),
        }
        for item in sessions
    ]


@router.get('/sessions/{session_id}')
def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    repository = ChatRepository(db)
    session = repository.get_session(session_id=session_id, user_id=user_id)
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')
    return {
        'id': session.id,
        'title': session.title,
        'created_at': session.created_at.isoformat(),
    }


@router.get('/sessions/{session_id}/messages')
def get_session_messages(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[dict]:
    repository = ChatRepository(db)
    session = repository.get_session(session_id=session_id, user_id=user_id)
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')
    messages = repository.list_recent_messages(session_id=session_id, limit=100)
    return [
        {
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'created_at': msg.created_at.isoformat(),
        }
        for msg in messages
    ]


@router.post('/sessions/{session_id}/messages', response_model=ChatResponseDTO)
def send_message(
    session_id: str,
    payload: ChatMessageCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> ChatResponseDTO:
    repository = ChatRepository(db)
    plan_repository = PlanRepository(db)
    session = repository.get_session(session_id=session_id, user_id=user_id)
    if not session:
        raise HTTPException(status_code=404, detail='Chat session not found')

    repository.add_message(session_id=session_id, role='user', content=payload.content)
    context = _build_chat_context(db=db, user_id=user_id, session_id=session_id, payload=payload)
    target_day = context['target_day']

    result = dayplanner_agent.run(
        user_input=payload.content,
        plan_date=target_day.isoformat(),
        memory_snippets=context['memory_snippets'],
        recent_messages=context['recent_messages'],
        existing_calendar_events=context['calendar_events'],
        previous_day_summary=context['previous_day_summary'],
        previous_day_blocks=context['previous_day_blocks'],
        llm_config=context['llm_config'],
        user_id=user_id,
        session_id=session_id,
    )

    saved_to_today = False
    if result['blocks'] and result.get('save_to_today', False):
        plan_repository.upsert_plan_for_day(
            user_id=user_id,
            day=target_day,
            summary=result['summary'],
            blocks=result['blocks'],
        )
        saved_to_today = True

    assistant_reply = result.get('assistant_reply') or result.get('summary') or 'I am ready to keep planning with you.'
    repository.add_message(session_id=session_id, role='assistant', content=assistant_reply)
    memory_service.store_preference_from_chat(user_id=user_id, user_message=payload.content)
    if result.get('save_to_today') and result.get('blocks'):
        signal = (
            f"User planned {len(result['blocks'])} blocks for {target_day.isoformat()}: "
            f"{result.get('summary', '')}"
        )
        memory_service.upsert_memory_from_signal(user_id=user_id, signal=signal, node_type='pattern')

    return ChatResponseDTO(
        message='DayPlannerAgent responded.',
        summary=result['summary'],
        assistant_reply=assistant_reply,
        saved_to_today=saved_to_today,
        needs_clarification=bool(result.get('needs_clarification', False)),
        follow_up_questions=result.get('follow_up_questions', []),
        blocks=[PlanBlockDTO(**block) for block in result['blocks']],
    )


@router.post('/sessions/{session_id}/messages/stream')
def send_message_stream(
    session_id: str,
    payload: ChatMessageCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    repository = ChatRepository(db)
    plan_repository = PlanRepository(db)
    session = repository.get_session(session_id=session_id, user_id=user_id)
    if not session:
        raise HTTPException(status_code=404, detail='Chat session not found')

    def event_generator():
        context = _build_chat_context(db=db, user_id=user_id, session_id=session_id, payload=payload)
        target_day = context['target_day']

        repository.add_message(session_id=session_id, role='user', content=payload.content)
        yield f"data: {json.dumps({'type': 'token', 'content': ''})}\n\n"

        try:
            result = dayplanner_agent.run(
                user_input=payload.content,
                plan_date=target_day.isoformat(),
                memory_snippets=context['memory_snippets'],
                recent_messages=context['recent_messages'],
                existing_calendar_events=context['calendar_events'],
                previous_day_summary=context['previous_day_summary'],
                previous_day_blocks=context['previous_day_blocks'],
                llm_config=context['llm_config'],
                user_id=user_id,
                session_id=session_id,
            )

            reply = result.get('assistant_reply', '') or result.get('summary', '')
            words = reply.split(' ')
            for index, word in enumerate(words):
                token = word + (' ' if index < len(words) - 1 else '')
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

            saved = False
            if result.get('blocks') and result.get('save_to_today'):
                plan_repository.upsert_plan_for_day(
                    user_id=user_id,
                    day=target_day,
                    summary=result.get('summary', ''),
                    blocks=result['blocks'],
                )
                saved = True

            yield f"data: {json.dumps({'type': 'plan', 'blocks': result.get('blocks', []), 'summary': result.get('summary', ''), 'saved': saved})}\n\n"

            repository.add_message(session_id=session_id, role='assistant', content=reply)
            memory_service.store_preference_from_chat(user_id=user_id, user_message=payload.content)
            if result.get('save_to_today') and result.get('blocks'):
                signal = (
                    f"User planned {len(result['blocks'])} blocks for {target_day.isoformat()}: "
                    f"{result.get('summary', '')}"
                )
                memory_service.upsert_memory_from_signal(user_id=user_id, signal=signal, node_type='pattern')

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )

from fastapi import APIRouter

from app.api.v1.routes import auth, calendar, chat, health, history, memory, plans, settings

api_router = APIRouter()
api_router.include_router(health.router, tags=['health'])
api_router.include_router(auth.router, prefix='/auth', tags=['auth'])
api_router.include_router(plans.router, prefix='/plans', tags=['plans'])
api_router.include_router(chat.router, prefix='/chat', tags=['chat'])
api_router.include_router(calendar.router, prefix='/calendar', tags=['calendar'])
api_router.include_router(history.router, prefix='/history', tags=['history'])
api_router.include_router(settings.router, prefix='/settings', tags=['settings'])
api_router.include_router(memory.router, prefix='/memory', tags=['memory'])

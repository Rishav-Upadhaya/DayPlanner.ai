import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

RATE_LIMITS = {
    'chat': {'free': 20, 'pro': 200, 'team': 500},
    'plans': {'free': 10, 'pro': 100, 'team': 300},
}

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    from app.core.config import get_settings

    settings = get_settings()
    if not settings.redis_url:
        return None

    try:
        import redis

        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception as exc:
        logger.warning('Redis unavailable, rate limiting disabled: %s', exc)
        return None


def check_rate_limit(user_id: str, endpoint_type: str, tier: str = 'free') -> tuple[bool, int]:
    redis_client = _get_redis()
    if redis_client is None:
        return True, 0

    limit = RATE_LIMITS.get(endpoint_type, {}).get(tier, 20)
    key = f'rate:{endpoint_type}:{user_id}'
    now = int(time.time())
    window_start = now - 3600

    try:
        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {f'{now}:{time.time_ns()}': now})
        pipe.zcard(key)
        pipe.expire(key, 3600)
        _, _, count, _ = pipe.execute()

        if count > limit:
            oldest = redis_client.zrange(key, 0, 0, withscores=True)
            retry_after = 3600 - (now - int(oldest[0][1])) if oldest else 60
            return False, max(1, retry_after)
        return True, 0
    except Exception:
        return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    RATE_LIMIT_PATHS = {
        '/api/v1/chat/': 'chat',
        '/api/v1/plans/generate': 'plans',
    }

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        endpoint_type = None
        for prefix, ep_type in self.RATE_LIMIT_PATHS.items():
            if path.startswith(prefix):
                endpoint_type = ep_type
                break

        if endpoint_type:
            user_id = request.headers.get('X-User-Id', '')
            if user_id:
                allowed, retry_after = check_rate_limit(user_id, endpoint_type)
                if not allowed:
                    from fastapi.responses import JSONResponse

                    return JSONResponse(
                        status_code=429,
                        content={'detail': 'Rate limit exceeded'},
                        headers={'Retry-After': str(retry_after)},
                    )

        return await call_next(request)

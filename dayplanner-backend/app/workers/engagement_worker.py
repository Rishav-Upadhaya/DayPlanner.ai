import threading

from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.services.engagement import EngagementPromptService

_worker_thread: threading.Thread | None = None
_stop_event: threading.Event | None = None
_leader_connection = None


def _run_loop() -> None:
    settings = get_settings()
    interval = max(30, settings.background_sync_interval_seconds)

    while _stop_event is not None and not _stop_event.is_set():
        db = SessionLocal()
        try:
            service = EngagementPromptService(db=db)
            service.run_once()
        except Exception:
            pass
        finally:
            db.close()

        _stop_event.wait(timeout=interval)


def start_engagement_worker() -> None:
    global _worker_thread, _stop_event, _leader_connection

    settings = get_settings()
    if not settings.enable_background_sync:
        return

    if _worker_thread and _worker_thread.is_alive():
        return

    if settings.enable_background_sync_leader_lock:
        acquired = False
        lock_id = settings.background_sync_leader_lock_id + 1
        try:
            _leader_connection = engine.connect()
            if engine.dialect.name == 'postgresql':
                row = _leader_connection.execute(
                    text('SELECT pg_try_advisory_lock(:lock_id)'),
                    {'lock_id': lock_id},
                ).first()
                acquired = bool(row and row[0])
            else:
                acquired = True
        except Exception:
            acquired = False

        if not acquired:
            if _leader_connection is not None:
                _leader_connection.close()
                _leader_connection = None
            return

    _stop_event = threading.Event()
    _worker_thread = threading.Thread(target=_run_loop, name='engagement-worker', daemon=True)
    _worker_thread.start()


def stop_engagement_worker() -> None:
    global _worker_thread, _stop_event, _leader_connection

    settings = get_settings()

    if _stop_event is not None:
        _stop_event.set()

    if _worker_thread is not None and _worker_thread.is_alive():
        _worker_thread.join(timeout=2)

    if _leader_connection is not None:
        try:
            if engine.dialect.name == 'postgresql' and settings.enable_background_sync_leader_lock:
                _leader_connection.execute(
                    text('SELECT pg_advisory_unlock(:lock_id)'),
                    {'lock_id': settings.background_sync_leader_lock_id + 1},
                )
        except Exception:
            pass
        finally:
            _leader_connection.close()
            _leader_connection = None

    _worker_thread = None
    _stop_event = None

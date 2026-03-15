from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(settings.database_url, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def run_startup_schema_migrations() -> None:
    with engine.begin() as connection:
        inspector = inspect(connection)
        tables = set(inspector.get_table_names())

        if 'users' in tables:
            existing_columns = {column['name'] for column in inspector.get_columns('users')}
            if 'password_hash' not in existing_columns:
                connection.execute(text('ALTER TABLE users ADD COLUMN password_hash VARCHAR(255)'))
            if 'avatar_url' not in existing_columns:
                connection.execute(text('ALTER TABLE users ADD COLUMN avatar_url VARCHAR(512)'))
            if 'google_sub' not in existing_columns:
                connection.execute(text('ALTER TABLE users ADD COLUMN google_sub VARCHAR(255)'))

        if 'calendar_conflicts' in tables:
            conflict_columns = {column['name'] for column in inspector.get_columns('calendar_conflicts')}
            if 'day' not in conflict_columns:
                connection.execute(text('ALTER TABLE calendar_conflicts ADD COLUMN day DATE'))
                connection.execute(text("UPDATE calendar_conflicts SET day = CURRENT_DATE WHERE day IS NULL"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

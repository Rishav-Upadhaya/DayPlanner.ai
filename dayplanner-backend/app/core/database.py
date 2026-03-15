from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(settings.database_url, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def prepare_legacy_database_for_alembic(alembic_cfg: Config) -> bool:
    with engine.begin() as connection:
        if connection.dialect.name == 'postgresql':
            connection.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))

        inspector = inspect(connection)
        tables = set(inspector.get_table_names())

        version_rows = 0
        if 'alembic_version' in tables:
            version_rows = connection.execute(text('SELECT COUNT(*) FROM alembic_version')).scalar() or 0

    app_tables = tables - {'alembic_version'}

    if not app_tables:
        return False

    if 'alembic_version' in tables and version_rows > 0:
        return False

    Base.metadata.create_all(bind=engine)
    command.stamp(alembic_cfg, 'head')
    return True


def run_startup_schema_migrations() -> None:
    with engine.begin() as connection:
        if connection.dialect.name == 'postgresql':
            connection.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))

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

        if connection.dialect.name == 'postgresql' and 'memory_embeddings' in tables:
            embedding_cols = {column['name'] for column in inspector.get_columns('memory_embeddings')}
            if 'embedding' not in embedding_cols:
                connection.execute(text(
                    'ALTER TABLE memory_embeddings ADD COLUMN IF NOT EXISTS embedding vector(384)'
                ))
            if 'vector_ref' in embedding_cols:
                connection.execute(text(
                    'ALTER TABLE memory_embeddings DROP COLUMN IF EXISTS vector_ref'
                ))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

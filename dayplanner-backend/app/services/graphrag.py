from dataclasses import dataclass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.memory import MemoryNode


@dataclass
class MemoryContext:
    snippets: list[str]


class GraphRAGService:
    def retrieve_user_context(self, user_id: str, query: str) -> MemoryContext:
        del query
        db = SessionLocal()
        try:
            stmt = (
                select(MemoryNode)
                .where(MemoryNode.user_id == user_id)
                .order_by(MemoryNode.created_at.desc())
                .limit(8)
            )
            rows = list(db.scalars(stmt).all())
            snippets = [row.content for row in rows if row.content]
            return MemoryContext(snippets=snippets)
        finally:
            db.close()

    def upsert_memory_from_signal(self, user_id: str, signal: str) -> None:
        return None

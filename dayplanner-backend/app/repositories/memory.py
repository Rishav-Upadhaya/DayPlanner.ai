from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.memory import MemoryNode


class MemoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_nodes(self, user_id: str) -> list[MemoryNode]:
        stmt = select(MemoryNode).where(MemoryNode.user_id == user_id).order_by(MemoryNode.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def add_node(self, user_id: str, node_type: str, content: str, confidence: str = 'medium') -> MemoryNode:
        node = MemoryNode(user_id=user_id, node_type=node_type, content=content, confidence=confidence)
        self.db.add(node)
        self.db.commit()
        self.db.refresh(node)
        return node

    def delete_node(self, user_id: str, node_id: str) -> bool:
        stmt = delete(MemoryNode).where(MemoryNode.id == node_id, MemoryNode.user_id == user_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return bool(result.rowcount)

    def clear_nodes(self, user_id: str) -> int:
        stmt = delete(MemoryNode).where(MemoryNode.user_id == user_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return int(result.rowcount or 0)

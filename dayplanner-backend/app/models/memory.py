from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MemoryNode(Base):
    __tablename__ = 'memory_nodes'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'), index=True)
    node_type: Mapped[str] = mapped_column(String(64))
    content: Mapped[str] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(String(16), default='medium')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MemoryEdge(Base):
    __tablename__ = 'memory_edges'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey('users.id'), index=True)
    from_node_id: Mapped[str] = mapped_column(String(36), ForeignKey('memory_nodes.id'))
    to_node_id: Mapped[str] = mapped_column(String(36), ForeignKey('memory_nodes.id'))
    relation_type: Mapped[str] = mapped_column(String(64))


class MemoryEmbedding(Base):
    __tablename__ = 'memory_embeddings'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    node_id: Mapped[str] = mapped_column(String(36), ForeignKey('memory_nodes.id'), index=True)
    embedding_model: Mapped[str] = mapped_column(String(64), default='text-embedding-3-small')
    vector_ref: Mapped[str] = mapped_column(Text, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

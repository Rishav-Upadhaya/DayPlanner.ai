from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.memory import MemoryEmbedding, MemoryNode

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_embedding_model():
    try:
        from sentence_transformers import SentenceTransformer

        logger.info('Loading embedding model all-MiniLM-L6-v2...')
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info('Embedding model loaded.')
        return model
    except Exception as exc:
        logger.error('Failed to load embedding model: %s', exc)
        return None


def _embed(text_input: str) -> list[float] | None:
    model = _get_embedding_model()
    if model is None:
        return None
    try:
        vector = model.encode(text_input, normalize_embeddings=True)
        return vector.tolist()
    except Exception as exc:
        logger.warning('Embedding failed for input: %s', exc)
        return None


@dataclass
class MemoryContext:
    snippets: list[str]


class GraphRAGService:
    def retrieve_user_context(self, user_id: str, query: str) -> MemoryContext:
        db = SessionLocal()
        try:
            query_vector = _embed(query)
            if query_vector is not None and db.bind is not None and db.bind.dialect.name == 'postgresql':
                snippets = self._vector_search(db, user_id, query_vector, limit=10)
            else:
                snippets = self._recency_fallback(db, user_id, limit=8)
            return MemoryContext(snippets=snippets)
        finally:
            db.close()

    def _vector_search(self, db: Session, user_id: str, query_vector: list[float], limit: int) -> list[str]:
        try:
            sql = text(
                """
                SELECT mn.content
                FROM memory_embeddings me
                JOIN memory_nodes mn ON mn.id = me.node_id
                WHERE mn.user_id = :user_id
                  AND me.embedding IS NOT NULL
                ORDER BY me.embedding <=> CAST(:query_vec AS vector)
                LIMIT :limit
                """
            )
            rows = db.execute(
                sql,
                {
                    'user_id': user_id,
                    'query_vec': str(query_vector),
                    'limit': limit,
                },
            ).fetchall()
            return [row[0] for row in rows if row[0]]
        except Exception as exc:
            logger.warning('Vector search failed, falling back to recency: %s', exc)
            return self._recency_fallback(db, user_id, limit=limit)

    def _recency_fallback(self, db: Session, user_id: str, limit: int) -> list[str]:
        stmt = (
            select(MemoryNode)
            .where(MemoryNode.user_id == user_id)
            .order_by(MemoryNode.created_at.desc())
            .limit(limit)
        )
        rows = list(db.scalars(stmt).all())
        return [row.content for row in rows if row.content]

    def _store_embedding_for_node(self, db: Session, node_id: str, content: str) -> None:
        vector = _embed(content)
        if vector is None:
            return
        if db.bind is None or db.bind.dialect.name != 'postgresql':
            return
        embedding = MemoryEmbedding(
            node_id=node_id,
            embedding_model='all-MiniLM-L6-v2',
            embedding=vector,
        )
        db.add(embedding)

    def upsert_memory_from_signal(self, user_id: str, signal: str, node_type: str = 'note', confidence: str = 'medium') -> None:
        if not signal or not signal.strip():
            return

        db = SessionLocal()
        try:
            node = MemoryNode(
                user_id=user_id,
                node_type=node_type,
                content=signal.strip(),
                confidence=confidence,
            )
            db.add(node)
            db.flush()

            self._store_embedding_for_node(db, node.id, signal)
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning('Failed to store memory embedding: %s', exc)
        finally:
            db.close()

    def store_embedding_for_existing_node(self, node_id: str, content: str) -> None:
        if not node_id or not content.strip():
            return
        db = SessionLocal()
        try:
            self._store_embedding_for_node(db, node_id, content)
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning('Failed to store embedding for existing node: %s', exc)
        finally:
            db.close()

    def store_completion_memory(self, user_id: str, plan_date: str, completed: int, total: int, block_titles: list[str]) -> None:
        if not block_titles:
            return
        pct = int((completed / total) * 100) if total else 0
        signal = (
            f'On {plan_date}, completed {completed}/{total} tasks ({pct}%). '
            f'Completed: {", ".join(block_titles[:5])}.'
        )
        self.upsert_memory_from_signal(user_id, signal, node_type='completion', confidence='high')

    def store_preference_from_chat(self, user_id: str, user_message: str) -> None:
        preference_keywords = [
            'i prefer',
            'i like',
            'i always',
            'i never',
            'i usually',
            'mornings are',
            'evenings are',
            'my best time',
            'i work best',
            'i hate',
            'i love',
            'please always',
            'please never',
        ]
        msg_lower = user_message.lower()
        if any(keyword in msg_lower for keyword in preference_keywords):
            self.upsert_memory_from_signal(
                user_id,
                user_message.strip(),
                node_type='preference',
                confidence='medium',
            )

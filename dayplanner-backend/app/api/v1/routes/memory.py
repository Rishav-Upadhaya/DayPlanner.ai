from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user_id
from app.core.database import get_db
from app.repositories.memory import MemoryRepository
from app.schemas.memory import MemoryContextResponse, MemoryCreateDTO, MemoryItemDTO
from app.services.graphrag import GraphRAGService

router = APIRouter()
graph_rag = GraphRAGService()


@router.get('/context')
def get_memory_context(
    query: str = 'today planning',
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> MemoryContextResponse:
    repository = MemoryRepository(db)
    nodes = repository.list_nodes(user_id=user_id)
    context = graph_rag.retrieve_user_context(user_id=user_id, query=query)
    return MemoryContextResponse(
        snippets=context.snippets,
        items=[
            MemoryItemDTO(
                id=node.id,
                node_type=node.node_type,
                content=node.content,
                confidence=node.confidence,
            )
            for node in nodes
        ],
    )


@router.post('/context', response_model=MemoryItemDTO)
def add_memory_context(
    payload: MemoryCreateDTO,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> MemoryItemDTO:
    repository = MemoryRepository(db)
    node = repository.add_node(
        user_id=user_id,
        node_type=payload.node_type,
        content=payload.content,
        confidence=payload.confidence,
    )
    graph_rag.store_embedding_for_existing_node(node_id=node.id, content=payload.content)
    return MemoryItemDTO(id=node.id, node_type=node.node_type, content=node.content, confidence=node.confidence)


@router.delete('/context/{memory_id}')
def delete_memory_context(memory_id: str, user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> dict[str, str]:
    repository = MemoryRepository(db)
    deleted = repository.delete_node(user_id=user_id, node_id=memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail='Memory item not found')
    return {'status': 'deleted', 'memory_id': memory_id}


@router.post('/reset')
def reset_memory(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)) -> dict[str, str]:
    repository = MemoryRepository(db)
    deleted_count = repository.clear_nodes(user_id=user_id)
    return {'status': 'memory_reset_completed', 'user_id': user_id, 'deleted_items': str(deleted_count)}

from app.agents.langgraph_agent.state import AgentState
from app.services.graphrag import GraphRAGService

_rag = GraphRAGService()


class MemoryRetrievalNode:
    def run(self, state: AgentState) -> dict:
        entities = state.get('entities', {})
        tasks = entities.get('tasks', []) if isinstance(entities, dict) else []
        query = f"{state.get('intent', '')} {state.get('user_input', '')} {' '.join(tasks)}"
        user_id = state.get('user_id', '')
        if not user_id:
            return {'memory_snippets': state.get('memory_snippets', [])}

        context = _rag.retrieve_user_context(user_id=user_id, query=query.strip())
        preferences = _rag.retrieve_preference_context(user_id=user_id, limit=6)

        combined: list[str] = []
        seen: set[str] = set()
        for snippet in preferences + context.snippets:
            normalized = str(snippet).strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            combined.append(normalized)

        return {'memory_snippets': combined[:12]}

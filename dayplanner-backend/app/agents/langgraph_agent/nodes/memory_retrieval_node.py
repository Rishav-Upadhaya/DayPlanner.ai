from app.agents.langgraph_agent.state import AgentState
from app.services.graphrag import GraphRAGService

_rag = GraphRAGService()


class MemoryRetrievalNode:
    def run(self, state: AgentState) -> dict:
        entities = state.get('entities', {})
        tasks = entities.get('tasks', []) if isinstance(entities, dict) else []
        query = f"{state.get('intent', '')} {state.get('user_input', '')} {' '.join(tasks)}"
        context = _rag.retrieve_user_context(user_id=state['user_id'], query=query.strip())
        return {'memory_snippets': context.snippets}

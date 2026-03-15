from app.agents.langgraph_agent.state import AgentState
from app.services.graphrag import GraphRAGService

_rag = GraphRAGService()


class MemoryWriterNode:
    def run(self, state: AgentState) -> dict:
        user_id = state['user_id']
        _rag.store_preference_from_chat(user_id=user_id, user_message=state.get('user_input', ''))

        blocks = state.get('blocks', [])
        if blocks and state.get('save_to_today'):
            signal = (
                f"Generated {len(blocks)}-block plan for {state.get('plan_date', 'today')}: "
                f"{state.get('summary', '')}. "
                f"Tasks: {', '.join(block.get('title', '') for block in blocks[:5])}."
            )
            _rag.upsert_memory_from_signal(user_id, signal, node_type='pattern')

        return {}

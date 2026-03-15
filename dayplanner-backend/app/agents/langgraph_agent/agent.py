from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.langgraph_agent.llm_initializer import initialize_llm_gateway
from app.agents.langgraph_agent.nodes import ReasonAndRespondNode
from app.agents.langgraph_agent.nodes.calendar_node import CalendarReaderNode
from app.agents.langgraph_agent.nodes.intent_node import IntentClassifierNode
from app.agents.langgraph_agent.nodes.memory_retrieval_node import MemoryRetrievalNode
from app.agents.langgraph_agent.nodes.memory_writer_node import MemoryWriterNode
from app.agents.langgraph_agent.state import AgentState


def _route_by_intent(state: AgentState) -> str:
    intent = state.get('intent', 'new_plan')
    if intent == 'follow_up':
        return 'follow_up'
    return 'retrieve'


class DayPlannerAgent:
    def __init__(self) -> None:
        llm_gateway = initialize_llm_gateway()
        self.llm = llm_gateway

        intent_node = IntentClassifierNode(llm_gateway)
        memory_node = MemoryRetrievalNode()
        calendar_node = CalendarReaderNode()
        reason_node = ReasonAndRespondNode(llm_gateway)
        memory_writer = MemoryWriterNode()

        graph = StateGraph(AgentState)

        graph.add_node('intent_classifier', intent_node.run)
        graph.add_node('memory_retriever', memory_node.run)
        graph.add_node('calendar_reader', calendar_node.run)
        graph.add_node('reason_and_respond', reason_node.run)
        graph.add_node('memory_writer', memory_writer.run)

        graph.set_entry_point('intent_classifier')
        graph.add_conditional_edges(
            'intent_classifier',
            _route_by_intent,
            {
                'retrieve': 'memory_retriever',
                'follow_up': 'reason_and_respond',
            },
        )
        graph.add_edge('memory_retriever', 'calendar_reader')
        graph.add_edge('calendar_reader', 'reason_and_respond')
        graph.add_edge('reason_and_respond', 'memory_writer')
        graph.add_edge('memory_writer', END)
        self.graph = graph.compile()

    def run(
        self,
        *,
        user_input: str,
        plan_date: str,
        memory_snippets: list[str],
        recent_messages: list[dict[str, str]],
        existing_calendar_events: list[dict[str, str]],
        previous_day_summary: str = '',
        previous_day_blocks: list[dict[str, Any]] | None = None,
        llm_config: dict[str, str],
        user_id: str = '',
        session_id: str = '',
    ) -> dict[str, Any]:
        prev_blocks = previous_day_blocks or []
        result = self.graph.invoke(
            {
                'user_id': user_id,
                'session_id': session_id,
                'user_input': user_input,
                'plan_date': plan_date,
                'memory_snippets': memory_snippets,
                'messages': recent_messages,
                'recent_messages': recent_messages,
                'existing_calendar_events': existing_calendar_events,
                'previous_day_summary': previous_day_summary,
                'previous_day_blocks': prev_blocks,
                'llm_config': llm_config,
                'intent': '',
                'entities': {},
                'assistant_reply': '',
                'summary': '',
                'blocks': [],
                'save_to_today': False,
                'needs_clarification': False,
                'follow_up_questions': [],
                'error': None,
            }
        )
        return {
            'assistant_reply': result.get('assistant_reply', ''),
            'summary': result.get('summary', ''),
            'blocks': result.get('blocks', []),
            'save_to_today': bool(result.get('save_to_today', False)),
            'needs_clarification': bool(result.get('needs_clarification', False)),
            'follow_up_questions': result.get('follow_up_questions', []),
        }

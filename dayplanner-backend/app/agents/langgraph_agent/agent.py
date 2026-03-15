from typing import Any

from langgraph.graph import END, StateGraph

from app.agents.langgraph_agent.llm_initializer import initialize_llm_gateway
from app.agents.langgraph_agent.nodes import ReasonAndRespondNode
from app.agents.langgraph_agent.state import AgentState


class DayPlannerAgent:
    def __init__(self) -> None:
        llm_gateway = initialize_llm_gateway()
        self.llm = llm_gateway
        self._reason_and_respond_node = ReasonAndRespondNode(llm_gateway)

        graph = StateGraph(AgentState)
        graph.add_node('reason_and_respond', self._reason_and_respond_node.run)
        graph.set_entry_point('reason_and_respond')
        graph.add_edge('reason_and_respond', END)
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
    ) -> dict[str, Any]:
        prev_blocks = previous_day_blocks or []
        result = self.graph.invoke(
            {
                'user_input': user_input,
                'plan_date': plan_date,
                'memory_snippets': memory_snippets,
                'recent_messages': recent_messages,
                'existing_calendar_events': existing_calendar_events,
                'previous_day_summary': previous_day_summary,
                'previous_day_blocks': prev_blocks,
                'llm_config': llm_config,
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

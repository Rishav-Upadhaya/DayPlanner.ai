import json

from app.agents.langgraph_agent.state import AgentState
from app.integrations.llm_client import AgentLLMGateway

INTENT_SYSTEM = """Classify the user's planning intent. Return ONLY valid JSON.

Intents:
- new_plan: user wants to create or regenerate a full day plan
- continue: user wants to add, edit, or adjust an existing plan
- follow_up: user is doing evening check-in, reporting completions, or reflecting
- conflict_resolve: user is resolving a scheduling conflict

Output format:
{
  "intent": "new_plan",
  "entities": {
    "tasks": ["list of mentioned tasks"],
    "times": ["any mentioned times"],
    "date": "today|tomorrow|specific date or null"
  }
}"""


class IntentClassifierNode:
    def __init__(self, llm_gateway: AgentLLMGateway) -> None:
        self.llm = llm_gateway

    def run(self, state: AgentState) -> dict:
        try:
            raw = self.llm.generate(
                system_prompt=INTENT_SYSTEM,
                user_prompt=f"Message: {state['user_input']}",
                **{
                    key: state['llm_config'].get(key, '')
                    for key in [
                        'primary_provider',
                        'primary_api_key',
                        'primary_model',
                        'fallback_provider',
                        'fallback_api_key',
                        'fallback_model',
                    ]
                },
            )
            clean = raw.strip().removeprefix('```json').removeprefix('```').removesuffix('```').strip()
            parsed = json.loads(clean)
            return {
                'intent': parsed.get('intent', 'new_plan'),
                'entities': parsed.get('entities', {}),
            }
        except Exception:
            return {'intent': 'new_plan', 'entities': {}}

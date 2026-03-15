from app.integrations.llm_client import AgentLLMGateway


def initialize_llm_gateway() -> AgentLLMGateway:
    return AgentLLMGateway()

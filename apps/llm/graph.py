"""LLM orchestration module.

Currently runs in mock mode. Replace with LangGraph implementation
when ready to connect a real LLM provider.
"""

from __future__ import annotations

import os


def run_agent(message: str) -> str:
    """Process a user message and return an assistant response.

    Uses mock mode by default. Set OPENAI_API_KEY or ANTHROPIC_API_KEY
    environment variable to enable real LLM calls (future).

    Args:
        message: The user's input message.

    Returns:
        A response string from the (mock) assistant.
    """
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return _mock_response(message)

    # ------------------------------------------------------------------
    # TODO: LangGraph integration
    #
    # from langgraph.graph import StateGraph, END
    #
    # class GraphState(TypedDict):
    #     message: str
    #     response: str
    #
    # def process_input(state): ...
    # def generate_response(state): ...
    #
    # workflow = StateGraph(GraphState)
    # workflow.add_node("process", process_input)
    # workflow.add_node("generate", generate_response)
    # workflow.add_edge("process", "generate")
    # workflow.add_edge("generate", END)
    # workflow.set_entry_point("process")
    # graph = workflow.compile()
    # result = graph.invoke({"message": message})
    # return result["response"]
    # ------------------------------------------------------------------

    return _mock_response(message)


def _mock_response(message: str) -> str:
    """Return a deterministic mock response for development/testing."""
    return f"[MOCK] 입력을 받았습니다: {message[:80]}{'...' if len(message) > 80 else ''}"

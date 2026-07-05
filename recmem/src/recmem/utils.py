"""
Shared LLM wrapper.
Replace mock with real API call when ready (OpenAI/Anthropic).
"""

def call_llm(prompt: str) -> str:
    # TODO: replace with real LLM call before demo day
    # For now, default to INDEPENDENT so mock never falsely triggers contradiction/resolution
    return "INDEPENDENT"
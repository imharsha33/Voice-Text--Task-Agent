"""LLM provider package with support for current Groq provider and future VOXFLOW-LM extension point."""

from llm.base import BaseLLMProvider, LLMResponse, ToolCall
from llm.groq_provider import GroqLLMProvider
from llm.voxflow_lm_extension import VoxFlowLMProvider, BujjiLMProvider

# Alias
LLMProvider = BaseLLMProvider


def get_llm_provider() -> BaseLLMProvider:
    """Return default configured LLM provider."""
    return GroqLLMProvider()


__all__ = [
    "BaseLLMProvider",
    "LLMProvider",
    "LLMResponse",
    "ToolCall",
    "GroqLLMProvider",
    "VoxFlowLMProvider",
    "BujjiLMProvider",
    "get_llm_provider",
]

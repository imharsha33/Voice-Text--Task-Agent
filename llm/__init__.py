"""LLM provider package with support for current Groq provider and future BUJJI-LM extension point."""

from llm.base import BaseLLMProvider, LLMResponse, ToolCall
from llm.groq_provider import GroqLLMProvider
from llm.bujji_lm_extension import BujjiLMProvider

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
    "BujjiLMProvider",
    "get_llm_provider",
]

"""
base.py — Abstract Interface for LLM Providers
Defines standard signatures for model completions, streaming responses, and tool calling.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable, Iterator


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class LLMResponse:
    content: Optional[str]
    tool_calls: List[ToolCall]
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class BaseLLMProvider(ABC):
    """Abstract interface for LLM backends."""

    @abstractmethod
    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        chunk_callback: Optional[Callable[[str], None]] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048
    ) -> LLMResponse:
        """Generate response with optional streaming callback and tool calling."""
        pass

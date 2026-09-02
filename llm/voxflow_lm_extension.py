"""
voxflow_lm_extension.py — Extension Point for Future VOXFLOW-LM Integration
NOTE: VOXFLOW-LM is not ready yet. This module defines the architectural extension point
and interface contract for when VOXFLOW-LM weights / service become available.
Do not activate until VOXFLOW-LM model release is finalized.
"""

from typing import List, Dict, Any, Optional, Callable
from llm.base import BaseLLMProvider, LLMResponse


class VoxFlowLMProvider(BaseLLMProvider):
    """
    Extension point for the custom VOXFLOW-LM foundational reasoning model.
    Will be connected to the dedicated VoxFlow-LM inference backend upon release.
    """

    def __init__(self, endpoint_url: Optional[str] = None, api_key: Optional[str] = None):
        self.endpoint_url = endpoint_url
        self.api_key = api_key
        self.is_ready = False

    def generate(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        chunk_callback: Optional[Callable[[str], None]] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048
    ) -> LLMResponse:
        raise NotImplementedError(
            "VOXFLOW-LM is currently in development and not yet available for inference. "
            "Please use the default Groq LLM provider."
        )


# Backward compatibility alias
BujjiLMProvider = VoxFlowLMProvider

"""
bujji_lm_extension.py — Backward-compatibility forwarding shim for voxflow_lm_extension
"""

from llm.voxflow_lm_extension import VoxFlowLMProvider, BujjiLMProvider

__all__ = ["VoxFlowLMProvider", "BujjiLMProvider"]

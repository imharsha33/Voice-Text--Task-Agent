"""
agent_brain.py — Backward-compatibility forwarding module for core.brain
"""

from core.brain import AgentBrain, get_brain
from core.prompts import build_system_prompt, sanitize_voice_output

__all__ = ["AgentBrain", "get_brain", "build_system_prompt", "sanitize_voice_output"]

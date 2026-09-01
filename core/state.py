"""
state.py — Agent State Transitions and Telemetry
Defines states: IDLE, LISTENING, THINKING, ACTING, SPEAKING, ERROR.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class AgentState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    ACTING = "acting"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class AgentStatus:
    state: AgentState = AgentState.IDLE
    command: str = ""
    response: str = ""
    agent_active: bool = True
    error_message: Optional[str] = None

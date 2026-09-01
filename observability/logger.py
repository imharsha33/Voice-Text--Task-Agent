"""
logger.py — Centralized Structured Logging with Dashboard Broadcast
Provides unified logging to terminal and WebSocket subscribers.
"""

import time
from enum import Enum
from typing import Callable, Optional


class LogLevel(str, Enum):
    INFO = "info"
    VOICE = "voice"
    BRAIN = "brain"
    ACTION = "action"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


from typing import Callable, Optional, Dict

PREFIX_MAP: Dict[str, str] = {
    LogLevel.INFO.value:    "[INFO ]",
    LogLevel.VOICE.value:   "[VOICE]",
    LogLevel.BRAIN.value:   "[BRAIN]",
    LogLevel.ACTION.value:  "[ACT  ]",
    LogLevel.SUCCESS.value: "[OK   ]",
    LogLevel.ERROR.value:   "[ERROR]",
    LogLevel.WARNING.value: "[WARN ]",
}

_broadcast_callback: Optional[Callable[[str, str], None]] = None


def set_broadcast_callback(fn: Callable[[str, str], None]):
    """Set external broadcast callback (e.g. WebSocket logger)."""
    global _broadcast_callback
    _broadcast_callback = fn


def log(msg: str, level: str = "info"):
    """Log formatted message to stdout and broadcast to connected frontends."""
    normalized_level = level.lower()
    prefix = PREFIX_MAP.get(normalized_level, f"[{normalized_level.upper()}]")
    ts = time.strftime("%H:%M:%S")
    print(f"  {ts} {prefix} {msg}")

    if _broadcast_callback:
        try:
            _broadcast_callback(normalized_level, msg)
        except Exception:
            pass

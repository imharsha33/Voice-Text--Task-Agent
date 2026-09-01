"""
tts package — Unified TTS Factory and Queue Player
"""

import platform
from typing import Optional
from voice.tts.base import BaseTTS, TTSQueuePlayer

_tts_engine: Optional[BaseTTS] = None


def get_tts_engine() -> BaseTTS:
    """Return platform-appropriate Text-to-Speech engine."""
    global _tts_engine
    if _tts_engine is None:
        sys_name = platform.system().lower()
        if sys_name == "windows":
            from voice.tts.windows_tts import WindowsTTS
            _tts_engine = WindowsTTS()
        else:
            from voice.tts.macos_tts import MacOSTTS
            _tts_engine = MacOSTTS()
    return _tts_engine


def speak_async(text: str):
    """Speak text asynchronously."""
    get_tts_engine().speak(text, blocking=False)


def speak_sync(text: str):
    """Speak text synchronously."""
    get_tts_engine().speak(text, blocking=True)


__all__ = ["BaseTTS", "TTSQueuePlayer", "get_tts_engine", "speak_async", "speak_sync"]

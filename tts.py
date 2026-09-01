"""
tts.py — Backward-compatibility forwarding module for voice.tts
"""

from voice.tts import TTSQueuePlayer, get_tts_engine, speak_async, speak_sync


def speak(text: str, voice: str = "Samantha", rate: int = 180, blocking: bool = False):
    """Legacy speak wrapper."""
    if blocking:
        speak_sync(text)
    else:
        speak_async(text)


__all__ = ["speak", "speak_async", "speak_sync", "TTSQueuePlayer"]

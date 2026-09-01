"""
base.py — Abstract Base Class for Speech-to-Text (STT) Providers
"""

from abc import ABC, abstractmethod
import numpy as np


class SpeechToTextProvider(ABC):
    """Abstract interface for speech transcription engines."""

    @abstractmethod
    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe numpy audio data to text string."""
        pass


# Backward compatibility alias
BaseSTTProvider = SpeechToTextProvider

__all__ = ["SpeechToTextProvider", "BaseSTTProvider"]

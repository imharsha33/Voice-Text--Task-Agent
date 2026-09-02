"""
groq_whisper.py — Groq Whisper Cloud STT Provider
Sends in-memory WAV audio bytes to Groq Whisper API for low-latency speech transcription.
"""

import os
from typing import Optional
from groq import Groq
import numpy as np

from voice.stt.base import BaseSTTProvider
from voice.audio import numpy_to_wav_bytes


class GroqWhisperSTT(BaseSTTProvider):
    """Speech-to-Text provider powered by Groq's Whisper API."""

    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-large-v3-turbo"):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.client = Groq(api_key=self.api_key)

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio using Groq cloud API."""
        if len(audio_data) == 0:
            return ""

        wav_bytes = numpy_to_wav_bytes(audio_data, sr=sample_rate)
        if len(wav_bytes) < 1000:
            return ""

        try:
            transcription = self.client.audio.transcriptions.create(
                file=("audio.wav", wav_bytes, "audio/wav"),
                model=self.model,
                language="en",
                prompt="Hey Bujji, open Chrome, YouTube, search, play movie, music, volume, terminal, system.",
                response_format="text",
                temperature=0.0
            )
            return str(transcription).strip()
        except Exception as e:
            # Keep errors visible in stdout / stderr
            print(f"[GroqWhisperSTT] Transcription error: {e}")
            return ""

"""
audio.py — Audio Capture and Voice Activity Detection (VAD)
Cross-platform sound recording and RMS volume analysis using sounddevice and numpy.
"""

import io
import os
import queue
import wave
from typing import Optional
import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = np.int16


def audio_rms(audio: np.ndarray) -> float:
    """Calculate Root Mean Square (RMS) volume level of audio array."""
    if len(audio) == 0:
        return 0.0
    return float(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))


def record_audio_fixed(duration: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Record audio for fixed duration in seconds."""
    frames = int(duration * sr)
    audio = sd.rec(frames, samplerate=sr, channels=CHANNELS, dtype=DTYPE)
    sd.wait()
    return audio.flatten()


def record_until_silence(
    max_duration: float = 10.0,
    silence_rms: float = 150.0,
    silence_duration: float = 1.2,
    sr: int = SAMPLE_RATE
) -> np.ndarray:
    """
    Record audio until silence is detected or max_duration is reached.
    """
    chunk_duration = 0.3
    chunk_frames = int(chunk_duration * sr)
    all_audio = []
    silent_chunks = 0
    silent_chunks_needed = int(silence_duration / chunk_duration)
    max_chunks = int(max_duration / chunk_duration)
    audio_queue: queue.Queue = queue.Queue()

    def callback(indata, frames, time_info, status):
        audio_queue.put(indata.copy())

    with sd.InputStream(samplerate=sr, channels=CHANNELS, dtype=DTYPE,
                        blocksize=chunk_frames, callback=callback):
        chunks_recorded = 0
        while chunks_recorded < max_chunks:
            try:
                chunk = audio_queue.get(timeout=1.0)
                flat = chunk.flatten()
                all_audio.append(flat)
                chunks_recorded += 1
                if audio_rms(flat) < silence_rms:
                    silent_chunks += 1
                    if silent_chunks >= silent_chunks_needed and len(all_audio) > 3:
                        break
                else:
                    silent_chunks = 0
            except queue.Empty:
                break

    return np.concatenate(all_audio) if all_audio else np.zeros(sr, dtype=DTYPE)


def numpy_to_wav_bytes(audio: np.ndarray, sr: int = SAMPLE_RATE) -> bytes:
    """Convert numpy int16 audio array to standard WAV bytes."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio.tobytes())
    buf.seek(0)
    return buf.read()

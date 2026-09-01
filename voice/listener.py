"""
listener.py — Continuous Voice Listener Loop
Captures microphone audio, applies VAD silence detection, and transcribes commands via STT provider.
"""

import os
import time
import queue
import threading
from typing import Callable, Optional
import numpy as np
import sounddevice as sd

from voice.audio import audio_rms, numpy_to_wav_bytes, SAMPLE_RATE, CHANNELS, DTYPE
from voice.stt import BaseSTTProvider, GroqWhisperSTT


class VoiceListener:
    """Continuous voice listener with VAD silence detection."""

    def __init__(
        self,
        on_command_callback: Callable[[str], None],
        stt_provider: Optional[BaseSTTProvider] = None,
        wake_word: Optional[str] = None
    ):
        self.callback = on_command_callback
        self.stt = stt_provider or GroqWhisperSTT()
        self.wake_word = (wake_word or os.getenv("WAKE_WORD", "hey bujji")).lower()
        self.record_seconds = int(os.getenv("RECORD_SECONDS", "8"))
        self.silence_duration = float(os.getenv("SILENCE_DURATION", "0.8"))
        self.min_voice_rms = float(os.getenv("MIN_VOICE_RMS", "800"))

        self.running = False
        self.paused = False
        self.thread: Optional[threading.Thread] = None
        self.log_fn: Optional[Callable[[str], None]] = None

    def set_logger(self, log_fn: Callable[[str], None]):
        self.log_fn = log_fn

    def _log(self, msg: str):
        if self.log_fn is not None:
            self.log_fn(msg)
        else:
            print(msg)

    def pause(self):
        """Pause listening (e.g. while agent is speaking)."""
        self.paused = True

    def resume(self):
        """Resume listening."""
        self.paused = False

    def start(self):
        """Start the background listening thread."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop listening."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
            self.thread = None

    def _record_utterance(self) -> np.ndarray:
        """Record audio until voice stops or max duration is hit."""
        chunk_sec = 0.3
        chunk_frames = int(chunk_sec * SAMPLE_RATE)
        max_chunks = int(self.record_seconds / chunk_sec)
        silent_chunks_needed = int(self.silence_duration / chunk_sec)
        silence_threshold = self.min_voice_rms * 0.4

        audio_q: queue.Queue = queue.Queue()

        def audio_cb(indata, frames, time_info, status):
            audio_q.put(indata.copy())

        all_audio = []
        silent_chunks = 0

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=chunk_frames,
                callback=audio_cb
            ):
                while len(all_audio) < max_chunks and self.running:
                    try:
                        chunk = audio_q.get(timeout=0.5)
                        flat = chunk.flatten()
                        all_audio.append(flat)

                        if audio_rms(flat) < silence_threshold:
                            silent_chunks += 1
                            if silent_chunks >= silent_chunks_needed and len(all_audio) > 3:
                                break
                        else:
                            silent_chunks = 0
                    except queue.Empty:
                        break
        except Exception as e:
            self._log(f"Microphone recording error: {e}")

        return np.concatenate(all_audio) if all_audio else np.zeros(SAMPLE_RATE, dtype=DTYPE)

    def _listen_loop(self):
        """Continuous background listening loop."""
        chunk_frames = int(0.2 * SAMPLE_RATE)
        trigger_rms = self.min_voice_rms

        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue

            try:
                # 1. Listen for voice activity trigger
                buf = sd.rec(chunk_frames, samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=DTYPE)
                sd.wait()
                flat = buf.flatten()
                rms = audio_rms(flat)

                if rms > trigger_rms and not self.paused:
                    self._log(f"🎙️ Voice detected (RMS: {int(rms)}). Listening for command...")

                    # 2. Record full utterance
                    audio = self._record_utterance()

                    if len(audio) < SAMPLE_RATE * 0.5:
                        continue

                    # 3. Transcribe audio via STT
                    text = self.stt.transcribe(audio, sample_rate=SAMPLE_RATE)
                    clean_text = text.strip()

                    if clean_text:
                        self._log(f"🗣️ Transcribed: '{clean_text}'")

                        # Strip wake word if present — operate on lowercased copy
                        # to avoid Unicode byte-offset misalignment (BUG-09)
                        lower = clean_text.lower()
                        if lower.startswith(self.wake_word):
                            # Slice from the lowercased version, then re-apply
                            stripped_lower = lower[len(self.wake_word):].strip().lstrip(",.!? ")
                            clean_text = stripped_lower

                        if clean_text:
                            self.callback(clean_text)
                    else:
                        self._log("No speech recognized in audio clip.")

            except Exception as e:
                # BUG-01 fix: always log listen-loop errors so failures are visible
                self._log(f"⚠️ Listen loop error: {type(e).__name__}: {e}")
                if self.running and not self.paused:
                    time.sleep(0.5)

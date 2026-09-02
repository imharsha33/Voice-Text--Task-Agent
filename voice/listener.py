"""
listener.py — Continuous Voice Listener Loop
Captures microphone audio, applies VAD silence detection, and transcribes commands via STT provider.
"""

import os
import time
import queue
import threading
from collections import deque
from typing import Callable, Optional
import numpy as np
import sounddevice as sd

from voice.audio import audio_rms, numpy_to_wav_bytes, SAMPLE_RATE, CHANNELS, DTYPE
from voice.stt import BaseSTTProvider, GroqWhisperSTT


class VoiceListener:
    """Continuous voice listener with pre-roll buffering and VAD silence detection."""

    def __init__(
        self,
        on_command_callback: Callable[[str], None],
        stt_provider: Optional[BaseSTTProvider] = None,
        wake_word: Optional[str] = None
    ):
        self.callback = on_command_callback
        self.stt = stt_provider or GroqWhisperSTT()
        self.wake_word = (wake_word or os.getenv("WAKE_WORD", "hey voxflow")).lower()
        self.record_seconds = int(os.getenv("RECORD_SECONDS", "10"))
        self.silence_duration = float(os.getenv("SILENCE_DURATION", "1.2"))
        self.min_voice_rms = float(os.getenv("MIN_VOICE_RMS", "350"))

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
        """Standalone utterance recorder for backward compatibility."""
        chunk_sec = 0.2
        chunk_frames = int(chunk_sec * SAMPLE_RATE)
        max_chunks = int(self.record_seconds / chunk_sec)
        silent_chunks_needed = max(3, int(self.silence_duration / chunk_sec))
        silence_threshold = max(120.0, self.min_voice_rms * 0.35)

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
                            if silent_chunks >= silent_chunks_needed and len(all_audio) > 5:
                                break
                        else:
                            silent_chunks = 0
                    except queue.Empty:
                        break
        except Exception as e:
            self._log(f"Microphone recording error: {e}")

        return np.concatenate(all_audio) if all_audio else np.zeros(SAMPLE_RATE, dtype=DTYPE)

    def _listen_loop(self):
        """Continuous background listening loop with pre-roll buffer to prevent cutting words."""
        chunk_sec = 0.1  # 100ms chunks for high-fidelity VAD
        chunk_frames = int(chunk_sec * SAMPLE_RATE)
        pre_roll_chunks = max(6, int(0.6 / chunk_sec))  # 600ms pre-roll buffer
        pre_roll = deque(maxlen=pre_roll_chunks)

        audio_q: queue.Queue = queue.Queue()

        def audio_cb(indata, frames, time_info, status):
            if self.running and not self.paused:
                audio_q.put(indata.copy())

        while self.running:
            if self.paused:
                pre_roll.clear()
                while not audio_q.empty():
                    try:
                        audio_q.get_nowait()
                    except queue.Empty:
                        break
                time.sleep(0.1)
                continue

            try:
                with sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype=DTYPE,
                    blocksize=chunk_frames,
                    callback=audio_cb
                ):
                    is_recording = False
                    recorded_chunks = []
                    silent_chunks = 0
                    speech_chunks = 0

                    while self.running:
                        if self.paused:
                            pre_roll.clear()
                            is_recording = False
                            recorded_chunks = []
                            time.sleep(0.1)
                            break

                        try:
                            raw_chunk = audio_q.get(timeout=0.2)
                        except queue.Empty:
                            continue

                        flat = raw_chunk.flatten()
                        rms = audio_rms(flat)

                        trigger_rms = self.min_voice_rms
                        silence_threshold = max(120.0, trigger_rms * 0.35)
                        silent_chunks_needed = max(4, int(self.silence_duration / chunk_sec))
                        max_chunks = int(self.record_seconds / chunk_sec)
                        min_speech_chunks = max(3, int(0.5 / chunk_sec))

                        if not is_recording:
                            pre_roll.append(flat)
                            if rms >= trigger_rms:
                                is_recording = True
                                self._log(f"🎙️ Voice detected (RMS: {int(rms)}). Listening for command...")
                                # PREPEND the entire pre-roll buffer so the start of words is never cut off!
                                recorded_chunks = list(pre_roll)
                                silent_chunks = 0
                                speech_chunks = 1
                        else:
                            recorded_chunks.append(flat)
                            if rms < silence_threshold:
                                silent_chunks += 1
                                # Check if silence duration is met AND minimum speech duration captured
                                if silent_chunks >= silent_chunks_needed and len(recorded_chunks) >= min_speech_chunks:
                                    is_recording = False
                            else:
                                silent_chunks = 0
                                speech_chunks += 1

                            if len(recorded_chunks) >= max_chunks:
                                is_recording = False

                            if not is_recording:
                                # Utterance completed
                                pre_roll.clear()
                                audio = np.concatenate(recorded_chunks) if recorded_chunks else np.array([], dtype=DTYPE)
                                recorded_chunks = []

                                if len(audio) >= int(SAMPLE_RATE * 0.6) and speech_chunks >= 2:
                                    text = self.stt.transcribe(audio, sample_rate=SAMPLE_RATE)
                                    clean_text = text.strip()

                                    if clean_text:
                                        self._log(f"🗣️ Transcribed: '{clean_text}'")

                                        # Strip wake word if present
                                        lower = clean_text.lower()
                                        for w in [self.wake_word, "hey voxflow", "voxflow"]:
                                            if lower.startswith(w):
                                                clean_text = clean_text[len(w):].strip().lstrip(",.!? ")
                                                lower = clean_text.lower()
                                                break

                                        if clean_text:
                                            self.callback(clean_text)
                                            # Flush any audio queued while the callback was processing
                                            pre_roll.clear()
                                            while not audio_q.empty():
                                                try:
                                                    audio_q.get_nowait()
                                                except queue.Empty:
                                                    break
                                        else:
                                            self._log("Wake word detected without command.")
                                    else:
                                        self._log("No speech recognized in audio clip.")

            except Exception as e:
                self._log(f"⚠️ Listen loop error: {type(e).__name__}: {e}")
                if self.running and not self.paused:
                    time.sleep(0.5)

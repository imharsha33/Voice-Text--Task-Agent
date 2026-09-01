"""
base.py — Abstract TTS Interface & Concurrent Speech Queue Player
Provides thread-safe, sentence-by-sentence queue streaming to speech engines.
"""

from abc import ABC, abstractmethod
import queue
import threading
from typing import Optional


class TextToSpeechProvider(ABC):
    """Abstract Text-to-Speech provider interface."""

    @abstractmethod
    def speak(self, text: str, blocking: bool = False):
        """Speak text through platform audio synthesizer."""
        pass


# Backward compatibility alias
BaseTTS = TextToSpeechProvider


class TTSQueuePlayer:
    """
    Queue-based Text-to-Speech player that handles sentence-by-sentence
    parallel playback. It runs a worker thread in the background to speak
    sentences in order as they arrive, significantly reducing perceived latency.
    """

    def __init__(self, tts_engine: Optional[TextToSpeechProvider] = None):
        if tts_engine is None:
            from voice.tts import get_tts_engine
            tts_engine = get_tts_engine()
        self.tts = tts_engine
        self.queue: queue.Queue = queue.Queue()
        self.thread: Optional[threading.Thread] = None
        self.running = False

    def start(self):
        """Start the background speech playback thread."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while self.running:
            try:
                text = self.queue.get(timeout=0.1)
                if text is None:
                    self.queue.task_done()
                    break
                if text.strip():
                    self.tts.speak(text.strip(), blocking=True)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                pass

    def speak_sentence(self, text: str):
        """Queue a sentence to be spoken."""
        if text and text.strip():
            self.queue.put(text.strip())

    def stop(self, wait: bool = True):
        """
        Stop the speech queue player.
        If wait=True, block until all queued sentences have finished.
        """
        if wait:
            self.queue.join()
        self.running = False
        self.queue.put(None)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            self.thread = None


__all__ = ["TextToSpeechProvider", "BaseTTS", "TTSQueuePlayer"]

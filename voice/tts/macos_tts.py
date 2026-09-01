"""
macos_tts.py — macOS Built-in 'say' Text-to-Speech Engine
Zero-dependency voice feedback for macOS.
"""

import subprocess
import threading
from voice.tts.base import BaseTTS


class MacOSTTS(BaseTTS):
    """macOS Text-to-Speech implementation using /usr/bin/say."""

    def __init__(self, voice: str = "Samantha", rate: int = 180):
        self.voice = voice
        self.rate = rate

    def speak(self, text: str, blocking: bool = False):
        def _speak():
            try:
                subprocess.run(
                    ["say", "-v", self.voice, "-r", str(self.rate), text],
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(["say", text], check=True, capture_output=True)
                except Exception:
                    pass
            except Exception:
                pass

        if blocking:
            _speak()
        else:
            threading.Thread(target=_speak, daemon=True).start()

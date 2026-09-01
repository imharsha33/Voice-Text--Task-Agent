"""
windows_tts.py — Windows Text-to-Speech Engine
Uses PowerShell System.Speech.Synthesis with optional pyttsx3 fallback.
"""

import subprocess
import threading
from voice.tts.base import BaseTTS


class WindowsTTS(BaseTTS):
    """Windows Text-to-Speech implementation using SAPI5 via PowerShell."""

    def __init__(self, rate: int = 0):
        # SAPI rate is from -10 to 10. Default 0 is normal speed.
        self.rate = rate

    def speak(self, text: str, blocking: bool = False):
        def _speak():
            try:
                # Escape single quotes for PowerShell
                escaped = text.replace("'", "''").replace('"', '`"')
                ps_script = f"""
                Add-Type -AssemblyName System.Speech
                $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
                $synth.Rate = {self.rate}
                $synth.Speak('{escaped}')
                """
                subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                    capture_output=True,
                    timeout=20
                )
            except Exception:
                pass

        if blocking:
            _speak()
        else:
            threading.Thread(target=_speak, daemon=True).start()

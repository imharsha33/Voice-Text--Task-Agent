"""
test_backward_compat.py — Verifies backward compatibility of legacy module shims
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class TestBackwardCompatibility(unittest.TestCase):
    def test_agent_brain_shim(self):
        import agent_brain
        brain = agent_brain.get_brain()
        self.assertIsNotNone(brain)

    def test_tts_shim(self):
        import tts
        self.assertTrue(hasattr(tts, "speak_async"))
        self.assertTrue(hasattr(tts, "TTSQueuePlayer"))

    def test_voice_listener_shim(self):
        import voice_listener
        self.assertTrue(hasattr(voice_listener, "VoiceListener"))
        self.assertTrue(hasattr(voice_listener, "audio_rms"))

    def test_mac_tools_shim(self):
        import mac_tools
        self.assertTrue(hasattr(mac_tools, "MAC_TOOLS"))
        self.assertTrue(hasattr(mac_tools, "MAC_TOOL_FUNCTIONS"))
        self.assertTrue(callable(mac_tools.open_app))
        self.assertTrue(callable(mac_tools.set_volume))

    def test_browser_tools_shim(self):
        import browser_tools
        self.assertTrue(hasattr(browser_tools, "BROWSER_TOOLS"))
        self.assertTrue(callable(browser_tools.search_youtube))

    def test_server_shim(self):
        import server
        self.assertTrue(hasattr(server, "app"))
        self.assertTrue(hasattr(server, "start_server_background"))


if __name__ == "__main__":
    unittest.main()

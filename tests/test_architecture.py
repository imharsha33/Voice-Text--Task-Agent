"""
test_architecture.py — Comprehensive Unit & Integration Tests for Cross-Platform Bujji Architecture
"""

import sys
import os
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from platform_layer import get_platform
from platform_layer.base import BasePlatform, BaseAppController, BaseSystemController, BaseInputController
from platform_layer.windows import WindowsPlatform
from platform_layer.macos import MacOSPlatform
from observability import get_tracker, log
from tools.filesystem import write_file, read_file, list_files
from tools.registry import TOOL_DEFINITIONS, get_tool_map, execute_tool
from core.prompts import build_system_prompt, sanitize_voice_output
from core.brain import AgentBrain


class TestPlatformAbstractionLayer(unittest.TestCase):
    def test_platform_detection(self):
        plat = get_platform()
        self.assertIsInstance(plat, BasePlatform)
        self.assertIn(plat.os_name, ["macOS", "Windows"])
        self.assertIsInstance(plat.apps, BaseAppController)
        self.assertIsInstance(plat.system, BaseSystemController)
        self.assertIsInstance(plat.input, BaseInputController)

    def test_windows_platform_instantiation(self):
        win_plat = WindowsPlatform()
        self.assertEqual(win_plat.os_name, "Windows")
        self.assertIsInstance(win_plat.apps, BaseAppController)
        self.assertIsInstance(win_plat.system, BaseSystemController)
        self.assertIsInstance(win_plat.input, BaseInputController)

    def test_macos_platform_instantiation(self):
        mac_plat = MacOSPlatform()
        self.assertEqual(mac_plat.os_name, "macOS")
        self.assertIsInstance(mac_plat.apps, BaseAppController)
        self.assertIsInstance(mac_plat.system, BaseSystemController)
        self.assertIsInstance(mac_plat.input, BaseInputController)


class TestFilesystemTools(unittest.TestCase):
    def setUp(self):
        self.test_dir = PROJECT_ROOT / "scratch_test_dir"
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.test_file = self.test_dir / "sample.txt"

    def tearDown(self):
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_read_write_list(self):
        # 1. Write file
        res_write = write_file(str(self.test_file), "Hello from Cross-Platform Bujji!")
        self.assertIn("Successfully wrote", res_write)

        # 2. Read file
        content = read_file(str(self.test_file))
        self.assertEqual(content, "Hello from Cross-Platform Bujji!")

        # 3. List files
        list_res = list_files(str(self.test_dir))
        self.assertIn("sample.txt", list_res)


class TestToolRegistry(unittest.TestCase):
    def test_tool_definitions_schema(self):
        self.assertGreater(len(TOOL_DEFINITIONS), 15)
        for tool in TOOL_DEFINITIONS:
            self.assertEqual(tool["type"], "function")
            self.assertIn("name", tool["function"])
            self.assertIn("description", tool["function"])
            self.assertIn("parameters", tool["function"])

    def test_tool_mapping(self):
        tool_map = get_tool_map()
        self.assertIn("open_app", tool_map)
        self.assertIn("set_volume", tool_map)
        self.assertIn("write_file", tool_map)
        self.assertIn("read_file", tool_map)
        self.assertIn("search_youtube", tool_map)

    def test_execute_tool_telemetry(self):
        tracker = get_tracker()
        initial_history_len = len(tracker.tool_execution_history)
        res = execute_tool("sleep_delay", {"seconds": 0.1})
        self.assertIn("Waited 0.1 seconds", res)
        self.assertEqual(len(tracker.tool_execution_history), initial_history_len + 1)


class TestCoreBrainAndPrompts(unittest.TestCase):
    def test_sanitize_voice_output(self):
        raw = "```python\nprint('hello')\n```\nHere is **bold** text and `code` with [link](https://example.com)!"
        sanitized = sanitize_voice_output(raw)
        self.assertNotIn("```", sanitized)
        self.assertNotIn("**", sanitized)
        self.assertNotIn("`", sanitized)
        self.assertNotIn("https://", sanitized)
        self.assertIn("Here is bold text and code with link!", sanitized)

    def test_build_system_prompt(self):
        prompt = build_system_prompt()
        self.assertIn("CURRENT REAL-TIME SYSTEM CONTEXT", prompt)
        self.assertIn("Operating System", prompt)


class TestObservabilityTracker(unittest.TestCase):
    def test_token_tracker_summary(self):
        tracker = get_tracker()
        tracker.record_llm_call(
            model="llama-3.3-70b-versatile",
            prompt_tokens=150,
            completion_tokens=50,
            duration_ms=450.0
        )
        summary = tracker.get_summary()
        self.assertGreaterEqual(summary["total_llm_calls"], 1)
        self.assertGreaterEqual(summary["total_tokens"], 200)


if __name__ == "__main__":
    unittest.main()

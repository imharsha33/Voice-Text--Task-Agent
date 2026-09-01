"""
test_platform.py — Comprehensive Unit Tests for Platform Abstraction Layer (PAL)
Tests platform detection, capability queries, standard directory paths, safe shell execution,
and unsupported OS handling.
"""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from platform_layer import (
    get_platform,
    create_platform,
    PlatformType,
    PlatformCapabilities,
    UnsupportedPlatformError,
    BasePlatform,
    MacOSPlatform,
    WindowsPlatform,
    LinuxPlatform,
    UnsupportedPlatform,
)
from tools.shell import execute_safe_shell, is_dangerous_command
from observability.tracker import get_tracker


class TestPlatformDetection(unittest.TestCase):
    """Tests for platform detection, instantiation, and capabilities."""

    def test_default_platform_detection(self):
        """Verify host platform detection matches OS."""
        plat = get_platform()
        self.assertIsInstance(plat, BasePlatform)
        self.assertIn(plat.platform_type, [PlatformType.MACOS, PlatformType.WINDOWS, PlatformType.LINUX])

    def test_macos_platform_detection(self):
        """Verify macOS platform detection aliases and capabilities."""
        for alias in ["Darwin", "darwin", "macOS", "macos", "osx"]:
            plat = create_platform(alias)
            self.assertIsInstance(plat, MacOSPlatform)
            self.assertEqual(plat.platform_type, PlatformType.MACOS)
            self.assertEqual(plat.os_name, "macOS")
            self.assertTrue(plat.is_supported)
            self.assertTrue(plat.can_launch_apps)
            self.assertTrue(plat.can_run_shell)
            self.assertTrue(plat.can_take_screenshot)
            self.assertTrue(plat.can_notify)

    def test_windows_platform_detection(self):
        """Verify Windows platform detection aliases and capabilities."""
        for alias in ["Windows", "windows", "win32", "cygwin"]:
            plat = create_platform(alias)
            self.assertIsInstance(plat, WindowsPlatform)
            self.assertEqual(plat.platform_type, PlatformType.WINDOWS)
            self.assertEqual(plat.os_name, "Windows")
            self.assertTrue(plat.is_supported)
            self.assertTrue(plat.can_launch_apps)
            self.assertTrue(plat.can_run_shell)
            self.assertTrue(plat.can_take_screenshot)
            self.assertTrue(plat.can_notify)

    def test_linux_platform_detection_unsupported(self):
        """Verify Linux is classified as an unsupported/future platform with clear errors."""
        for alias in ["Linux", "linux", "linux2", "gnu/linux"]:
            plat = create_platform(alias)
            self.assertIsInstance(plat, LinuxPlatform)
            self.assertEqual(plat.platform_type, PlatformType.LINUX)
            self.assertEqual(plat.os_name, "Linux")
            self.assertFalse(plat.is_supported)
            self.assertFalse(plat.can_launch_apps)
            self.assertFalse(plat.can_run_shell)
            self.assertFalse(plat.can_take_screenshot)
            self.assertFalse(plat.can_notify)

            # Test unsupported operations return clear errors
            open_res = plat.apps.open_application("chrome")
            self.assertIn("Error:", open_res)
            self.assertIn("not supported on Linux", open_res)

            shell_res = plat.run_shell_command("ls")
            self.assertIn("Error:", shell_res)
            self.assertIn("unsupported platform", shell_res)

            vol_res = plat.system.set_volume(50)
            self.assertIn("Error:", vol_res)

            notify_res = plat.system.show_notification("Test", "Message")
            self.assertIn("Error:", notify_res)

            scr_res = plat.input.take_screenshot()
            self.assertIn("Error:", scr_res)

    def test_generic_unsupported_platform(self):
        """Verify arbitrary unknown operating systems return clear unsupported errors."""
        plat = create_platform("FreeBSD")
        self.assertIsInstance(plat, UnsupportedPlatform)
        self.assertEqual(plat.platform_type, PlatformType.UNSUPPORTED)
        self.assertFalse(plat.is_supported)
        self.assertIn("Error:", plat.apps.open_application("calc"))
        self.assertIn("Error:", plat.run_shell_command("echo hello"))


class TestPlatformStandardDirectories(unittest.TestCase):
    """Tests standard path resolution using pathlib without hardcoded usernames."""

    def test_directory_paths_are_pathlib_instances(self):
        plat = get_platform()
        self.assertIsInstance(plat.home_dir, Path)
        self.assertIsInstance(plat.desktop_dir, Path)
        self.assertIsInstance(plat.documents_dir, Path)
        self.assertIsInstance(plat.downloads_dir, Path)
        self.assertIsInstance(plat.pictures_dir, Path)
        self.assertIsInstance(plat.videos_dir, Path)
        self.assertIsInstance(plat.music_dir, Path)

        # Paths must be absolute resolved paths
        self.assertTrue(plat.home_dir.is_absolute())
        self.assertTrue(plat.desktop_dir.is_absolute())
        self.assertTrue(plat.documents_dir.is_absolute())
        self.assertTrue(plat.downloads_dir.is_absolute())
        self.assertTrue(plat.pictures_dir.is_absolute())
        self.assertTrue(plat.videos_dir.is_absolute())
        self.assertTrue(plat.music_dir.is_absolute())

        # Subdirectories must be children of home_dir
        self.assertEqual(plat.desktop_dir.parent, plat.home_dir)
        self.assertEqual(plat.documents_dir.parent, plat.home_dir)
        self.assertEqual(plat.downloads_dir.parent, plat.home_dir)
        self.assertEqual(plat.pictures_dir.parent, plat.home_dir)
        self.assertEqual(plat.music_dir.parent, plat.home_dir)

    def test_capabilities_object(self):
        plat = get_platform()
        caps = plat.get_capabilities()
        self.assertIsInstance(caps, PlatformCapabilities)
        self.assertEqual(caps.os_name, plat.os_name)
        self.assertEqual(caps.home_dir, str(plat.home_dir))
        self.assertEqual(caps.desktop_dir, str(plat.desktop_dir))
        self.assertEqual(caps.documents_dir, str(plat.documents_dir))
        self.assertEqual(caps.downloads_dir, str(plat.downloads_dir))
        self.assertEqual(caps.pictures_dir, str(plat.pictures_dir))
        self.assertEqual(caps.videos_dir, str(plat.videos_dir))
        self.assertEqual(caps.music_dir, str(plat.music_dir))

        cap_dict = caps.to_dict()
        self.assertIn("os_name", cap_dict)
        self.assertIn("can_launch_apps", cap_dict)
        self.assertIn("home_dir", cap_dict)
        self.assertIn("pictures_dir", cap_dict)


class TestSafeShellExecution(unittest.TestCase):
    """Tests safe shell command execution and dangerous command protection."""

    def test_safe_command_execution(self):
        result = execute_safe_shell("echo 'hello from test'")
        self.assertEqual(result.exit_code, 0)
        self.assertIn("hello from test", result.stdout)
        self.assertFalse(result.blocked)
        self.assertFalse(result.is_destructive)

    def test_dangerous_command_detection_and_blocking(self):
        dangerous_cmds = [
            "rm -rf /some/directory",
            "del /s /q C:\\Users",
            "format D:",
            "shutdown -h now",
            "mkfs.ext4 /dev/sda1",
            ":(){ :|:& };:"
        ]
        for cmd in dangerous_cmds:
            is_danger, reason = is_dangerous_command(cmd)
            self.assertTrue(is_danger, f"Failed to detect dangerous command: {cmd}")

            # Verify blocked without confirmation
            res = execute_safe_shell(cmd, confirm=False)
            self.assertTrue(res.blocked)
            self.assertTrue(res.is_destructive)
            self.assertIn("Execution blocked", str(res.error))


class TestObservabilityTaskTracking(unittest.TestCase):
    """Tests task lifecycle and token tracking telemetry."""

    def test_task_start_and_finish(self):
        tracker = get_tracker()
        task_id = tracker.start_task("Test command")
        self.assertIsNotNone(task_id)
        self.assertIn(task_id, tracker.active_tasks)

        tracker.record_task_tool(
            task_id=task_id,
            tool_name="test_tool",
            arguments={"arg1": "val1"},
            duration_ms=15.0,
            success=True
        )

        tracker.record_task_llm(
            task_id=task_id,
            model="llama-3.3-70b-versatile",
            prompt_tokens=100,
            completion_tokens=50,
            duration_ms=250.0
        )

        tracker.finish_task(task_id=task_id, success=True)
        self.assertNotIn(task_id, tracker.active_tasks)
        self.assertTrue(any(t.task_id == task_id for t in tracker.task_history))


class TestMacOSBackwardCompatibility(unittest.TestCase):
    """Verifies existing macOS platform operations remain functional."""

    def test_macos_system_info(self):
        mac_plat = MacOSPlatform()
        info = mac_plat.system.get_system_info()
        self.assertIn("os", info)
        self.assertIn("home_dir", info)
        self.assertIn("desktop_dir", info)
        self.assertIn("documents_dir", info)
        self.assertIn("pictures_dir", info)


if __name__ == "__main__":
    unittest.main()

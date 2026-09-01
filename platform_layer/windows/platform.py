"""
platform.py — WindowsPlatform Implementation
Assembles WindowsAppController, WindowsSystemController, and WindowsInputController.
"""

import subprocess
from pathlib import Path
from typing import Optional

from platform_layer.base import BasePlatform, PlatformType
from platform_layer.windows.apps import WindowsAppController
from platform_layer.windows.system import WindowsSystemController
from platform_layer.windows.input import WindowsInputController


class WindowsPlatform(BasePlatform):
    """Concrete Platform implementation for Windows."""

    def __init__(self):
        self._apps = WindowsAppController()
        self._system = WindowsSystemController()
        self._input = WindowsInputController()

    @property
    def platform_type(self) -> PlatformType:
        return PlatformType.WINDOWS

    @property
    def os_name(self) -> str:
        return "Windows"

    @property
    def apps(self) -> WindowsAppController:
        return self._apps

    @property
    def system(self) -> WindowsSystemController:
        return self._system

    @property
    def input(self) -> WindowsInputController:
        return self._input

    def run_shell_command(self, command: str, cwd: Optional[Path] = None, timeout: int = 30) -> str:
        """Execute command safely in Windows cmd / powershell."""
        try:
            target_cwd = Path(cwd).expanduser().resolve() if cwd else Path.home()
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(target_cwd)
            )
            output = result.stdout.strip()
            errors = result.stderr.strip()

            if result.returncode == 0:
                return output if output else "Command executed successfully with no output."
            else:
                return f"Command returned exit code {result.returncode}:\n{errors or output}"
        except subprocess.TimeoutExpired:
            return f"Command timed out after {timeout} seconds."
        except Exception as e:
            return f"Error executing shell command: {str(e)}"

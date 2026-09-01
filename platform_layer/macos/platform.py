"""
platform.py — MacOSPlatform Implementation
Assembles MacOSAppController, MacOSSystemController, and MacOSInputController.
"""

import subprocess
import os
from pathlib import Path
from typing import Optional

from platform_layer.base import BasePlatform, PlatformType
from platform_layer.macos.apps import MacOSAppController
from platform_layer.macos.system import MacOSSystemController
from platform_layer.macos.input import MacOSInputController


class MacOSPlatform(BasePlatform):
    """Concrete Platform implementation for macOS."""

    def __init__(self):
        self._apps = MacOSAppController()
        self._system = MacOSSystemController()
        self._input = MacOSInputController()

    @property
    def platform_type(self) -> PlatformType:
        return PlatformType.MACOS

    @property
    def os_name(self) -> str:
        return "macOS"

    @property
    def apps(self) -> MacOSAppController:
        return self._apps

    @property
    def system(self) -> MacOSSystemController:
        return self._system

    @property
    def input(self) -> MacOSInputController:
        return self._input

    def run_shell_command(self, command: str, cwd: Optional[Path] = None, timeout: int = 30) -> str:
        """Execute zsh/bash command safely on macOS."""
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

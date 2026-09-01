"""
unsupported.py — Unsupported / Future Platform Implementations
Implements clear error reporting for unsupported OS targets (such as Linux).
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from platform_layer.base import (
    BasePlatform,
    BaseAppController,
    BaseSystemController,
    BaseInputController,
    PlatformType,
    UnsupportedPlatformError,
)


class UnsupportedAppController(BaseAppController):
    def __init__(self, platform_name: str):
        self.platform_name = platform_name

    def open_application(self, app_name: str) -> str:
        return f"Error: Application control ('open_application') is not supported on {self.platform_name}."

    def close_application(self, app_name: str, confirm: bool = False) -> str:
        return f"Error: Application control ('close_application') is not supported on {self.platform_name}."

    def application_exists(self, app_name: str) -> bool:
        return False

    def switch_to_app(self, app_name: str) -> str:
        return f"Error: Application switching ('switch_to_app') is not supported on {self.platform_name}."

    def get_running_apps(self) -> List[str]:
        return []

    def get_frontmost_app(self) -> str:
        return f"Unsupported ({self.platform_name})"


class UnsupportedSystemController(BaseSystemController):
    def __init__(self, platform_name: str):
        self.platform_name = platform_name

    def get_system_info(self) -> Dict[str, Any]:
        return {
            "os": f"{self.platform_name} (Unsupported / Future Platform)",
            "supported": False,
            "error": f"Detailed system inspection is not supported on {self.platform_name}."
        }

    def set_volume(self, level: int) -> str:
        return f"Error: Volume control is not supported on {self.platform_name}."

    def get_volume(self) -> str:
        return f"Error: Volume query is not supported on {self.platform_name}."

    def mute_audio(self) -> str:
        return f"Error: Audio muting is not supported on {self.platform_name}."

    def unmute_audio(self) -> str:
        return f"Error: Audio unmuting is not supported on {self.platform_name}."

    def set_brightness(self, level: int) -> str:
        return f"Error: Brightness control is not supported on {self.platform_name}."

    def lock_screen(self) -> str:
        return f"Error: Lock screen is not supported on {self.platform_name}."

    def sleep_system(self) -> str:
        return f"Error: System sleep is not supported on {self.platform_name}."

    def shutdown_system(self, confirm: bool = False) -> str:
        return f"Error: System shutdown is not supported on {self.platform_name}."

    def restart_system(self, confirm: bool = False) -> str:
        return f"Error: System restart is not supported on {self.platform_name}."

    def get_running_processes(self, limit: int = 30) -> List[Dict[str, Any]]:
        return []

    def open_settings(self, pane: str = "") -> str:
        return f"Error: Opening settings is not supported on {self.platform_name}."

    def empty_trash(self, confirm: bool = False) -> str:
        return f"Error: Empty trash/recycle bin is not supported on {self.platform_name}."

    def show_desktop(self) -> str:
        return f"Error: Desktop toggle is not supported on {self.platform_name}."

    def show_notification(self, title: str, message: str) -> str:
        return f"Error: Native notifications are not supported on {self.platform_name}."

    def create_note(self, title: str, body: str = "") -> str:
        return f"Error: Note creation is not supported on {self.platform_name}."

    def create_reminder(self, title: str, due_date: str = "") -> str:
        return f"Error: Reminders are not supported on {self.platform_name}."

    def open_file_manager(self, path: Optional[Path] = None) -> str:
        return f"Error: File manager is not supported on {self.platform_name}."


class UnsupportedInputController(BaseInputController):
    def __init__(self, platform_name: str):
        self.platform_name = platform_name

    def type_text(self, text: str, interval: float = 0.02) -> str:
        return f"Error: Synthetic keyboard typing is not supported on {self.platform_name}."

    def press_key(self, key_combo: str) -> str:
        return f"Error: Synthetic key press is not supported on {self.platform_name}."

    def click_at(self, x: int, y: int, button: str = "left", clicks: int = 1) -> str:
        return f"Error: Mouse clicks are not supported on {self.platform_name}."

    def double_click_at(self, x: int, y: int) -> str:
        return f"Error: Double click is not supported on {self.platform_name}."

    def right_click_at(self, x: int, y: int) -> str:
        return f"Error: Right click is not supported on {self.platform_name}."

    def move_mouse(self, x: int, y: int) -> str:
        return f"Error: Mouse movement is not supported on {self.platform_name}."

    def scroll(self, direction: str, amount: int = 4) -> str:
        return f"Error: Mouse scrolling is not supported on {self.platform_name}."

    def take_screenshot(self, save_path: Optional[Path] = None) -> str:
        return f"Error: Screenshot capture is not supported on {self.platform_name}."

    def get_screen_size(self) -> Dict[str, int]:
        return {"width": 0, "height": 0}

    def get_mouse_position(self) -> Dict[str, int]:
        return {"x": 0, "y": 0}

    def copy_to_clipboard(self, text: str) -> str:
        return f"Error: Clipboard control is not supported on {self.platform_name}."

    def get_clipboard(self) -> str:
        return ""


class LinuxPlatform(BasePlatform):
    """Linux Platform (classified as Unsupported / Future Platform)."""

    def __init__(self):
        self._name = "Linux"
        self._apps = UnsupportedAppController(self._name)
        self._system = UnsupportedSystemController(self._name)
        self._input = UnsupportedInputController(self._name)

    @property
    def platform_type(self) -> PlatformType:
        return PlatformType.LINUX

    @property
    def os_name(self) -> str:
        return "Linux"

    @property
    def is_supported(self) -> bool:
        return False

    @property
    def can_launch_apps(self) -> bool:
        return False

    @property
    def can_run_shell(self) -> bool:
        return False

    @property
    def can_take_screenshot(self) -> bool:
        return False

    @property
    def can_notify(self) -> bool:
        return False

    @property
    def apps(self) -> BaseAppController:
        return self._apps

    @property
    def system(self) -> BaseSystemController:
        return self._system

    @property
    def input(self) -> BaseInputController:
        return self._input

    def run_shell_command(self, command: str, cwd: Optional[Path] = None, timeout: int = 30) -> str:
        return f"Error: Shell execution is disabled on unsupported platform '{self.os_name}'."


class UnsupportedPlatform(BasePlatform):
    """Generic fallback for unknown/unsupported operating systems."""

    def __init__(self, name: str = "Unknown"):
        self._name = name
        self._apps = UnsupportedAppController(self._name)
        self._system = UnsupportedSystemController(self._name)
        self._input = UnsupportedInputController(self._name)

    @property
    def platform_type(self) -> PlatformType:
        return PlatformType.UNSUPPORTED

    @property
    def os_name(self) -> str:
        return self._name

    @property
    def is_supported(self) -> bool:
        return False

    @property
    def can_launch_apps(self) -> bool:
        return False

    @property
    def can_run_shell(self) -> bool:
        return False

    @property
    def can_take_screenshot(self) -> bool:
        return False

    @property
    def can_notify(self) -> bool:
        return False

    @property
    def apps(self) -> BaseAppController:
        return self._apps

    @property
    def system(self) -> BaseSystemController:
        return self._system

    @property
    def input(self) -> BaseInputController:
        return self._input

    def run_shell_command(self, command: str, cwd: Optional[Path] = None, timeout: int = 30) -> str:
        return f"Error: Shell execution is disabled on unsupported platform '{self.os_name}'."

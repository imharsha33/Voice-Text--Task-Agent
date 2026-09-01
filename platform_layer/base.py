"""
base.py — Abstract Base Classes for Platform Abstraction Layer (PAL)
Defines unified contracts for Apps, System, Input, OS directories, and capability queries.
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from pathlib import Path


class PlatformType(str, Enum):
    MACOS = "macos"
    WINDOWS = "windows"
    LINUX = "linux"
    UNSUPPORTED = "unsupported"


class UnsupportedPlatformError(Exception):
    """Raised when an unsupported platform or unsupported operation is invoked."""
    pass


class ConfirmationRequiredError(Exception):
    """Raised when a destructive or critical operation requires user confirmation."""
    pass


@dataclass
class PlatformCapabilities:
    """Represents the operational capabilities and paths of the host platform."""
    os_name: str
    platform_type: str
    is_supported: bool
    can_launch_apps: bool
    can_run_shell: bool
    can_take_screenshot: bool
    can_notify: bool
    home_dir: str
    desktop_dir: str
    documents_dir: str
    downloads_dir: str
    pictures_dir: str
    videos_dir: str
    music_dir: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BaseAppController(ABC):
    """Abstract interface for application lifecycle and window management."""

    @abstractmethod
    def open_application(self, app_name: str) -> str:
        """Launch or activate an application."""
        pass

    def open_app(self, app_name: str) -> str:
        """Alias for open_application."""
        return self.open_application(app_name)

    @abstractmethod
    def close_application(self, app_name: str, confirm: bool = False) -> str:
        """Close or terminate an application. Destructive closure may require confirmation."""
        pass

    def close_app(self, app_name: str, confirm: bool = False) -> str:
        """Alias for close_application."""
        return self.close_application(app_name, confirm=confirm)

    @abstractmethod
    def application_exists(self, app_name: str) -> bool:
        """Check whether an application exists or is installed on the host system."""
        pass

    @abstractmethod
    def switch_to_app(self, app_name: str) -> str:
        """Bring application to the foreground."""
        pass

    @abstractmethod
    def get_running_apps(self) -> List[str]:
        """Return list of names of running GUI applications."""
        pass

    @abstractmethod
    def get_frontmost_app(self) -> str:
        """Return name of currently focused application."""
        pass


class BaseSystemController(ABC):
    """Abstract interface for operating system hardware, audio, power, and settings."""

    @abstractmethod
    def get_system_info(self) -> Dict[str, Any]:
        """Retrieve OS version, CPU, RAM, battery, network, and standard directory paths."""
        pass

    @abstractmethod
    def set_volume(self, level: int) -> str:
        """Set master audio output volume (0 - 100)."""
        pass

    @abstractmethod
    def get_volume(self) -> str:
        """Get current master audio output volume."""
        pass

    @abstractmethod
    def mute_audio(self) -> str:
        """Mute master audio output."""
        pass

    @abstractmethod
    def unmute_audio(self) -> str:
        """Unmute master audio output."""
        pass

    @abstractmethod
    def set_brightness(self, level: int) -> str:
        """Set display brightness (0 - 100)."""
        pass

    @abstractmethod
    def lock_screen(self) -> str:
        """Lock workstation / user session."""
        pass

    @abstractmethod
    def sleep_system(self) -> str:
        """Put computer into sleep mode."""
        pass

    @abstractmethod
    def shutdown_system(self, confirm: bool = False) -> str:
        """Shut down the host computer. Requires explicit confirmation."""
        pass

    @abstractmethod
    def restart_system(self, confirm: bool = False) -> str:
        """Restart the host computer. Requires explicit confirmation."""
        pass

    @abstractmethod
    def get_running_processes(self, limit: int = 30) -> List[Dict[str, Any]]:
        """List active processes with PID, name, and CPU/memory if available."""
        pass

    @abstractmethod
    def open_settings(self, pane: str = "") -> str:
        """Open system configuration / settings app or specific subpane."""
        pass

    @abstractmethod
    def empty_trash(self, confirm: bool = False) -> str:
        """Empty recycle bin / trash. Requires confirmation."""
        pass

    @abstractmethod
    def show_desktop(self) -> str:
        """Minimize/hide open windows to reveal desktop."""
        pass

    @abstractmethod
    def show_notification(self, title: str, message: str) -> str:
        """Show native OS desktop banner notification."""
        pass

    @abstractmethod
    def create_note(self, title: str, body: str = "") -> str:
        """Create a quick system note."""
        pass

    @abstractmethod
    def create_reminder(self, title: str, due_date: str = "") -> str:
        """Create a system reminder."""
        pass

    @abstractmethod
    def open_file_manager(self, path: Optional[Path] = None) -> str:
        """Open native file manager (Finder on macOS, Explorer on Windows)."""
        pass


class BaseInputController(ABC):
    """Abstract interface for synthetic keyboard and mouse interactions."""

    @abstractmethod
    def type_text(self, text: str, interval: float = 0.02) -> str:
        """Type text string using synthetic keyboard events."""
        pass

    @abstractmethod
    def press_key(self, key_combo: str) -> str:
        """Press single key or hotkey combination (e.g. 'ctrl+c', 'command+space', 'enter')."""
        pass

    @abstractmethod
    def click_at(self, x: int, y: int, button: str = "left", clicks: int = 1) -> str:
        """Click mouse at screen coordinates (x, y)."""
        pass

    @abstractmethod
    def double_click_at(self, x: int, y: int) -> str:
        """Double-click mouse at (x, y)."""
        pass

    @abstractmethod
    def right_click_at(self, x: int, y: int) -> str:
        """Right-click mouse at (x, y)."""
        pass

    @abstractmethod
    def move_mouse(self, x: int, y: int) -> str:
        """Move mouse cursor to (x, y)."""
        pass

    @abstractmethod
    def scroll(self, direction: str, amount: int = 4) -> str:
        """Scroll wheel 'up' or 'down'."""
        pass

    @abstractmethod
    def take_screenshot(self, save_path: Optional[Path] = None) -> str:
        """Capture screen and save to disk image."""
        pass

    @abstractmethod
    def get_screen_size(self) -> Dict[str, int]:
        """Return {'width': int, 'height': int}."""
        pass

    @abstractmethod
    def get_mouse_position(self) -> Dict[str, int]:
        """Return {'x': int, 'y': int}."""
        pass

    @abstractmethod
    def copy_to_clipboard(self, text: str) -> str:
        """Copy text to OS clipboard."""
        pass

    @abstractmethod
    def get_clipboard(self) -> str:
        """Read text from OS clipboard."""
        pass


class BasePlatform(ABC):
    """Unified platform contract combining Apps, System, Input, OS directories, and Capability Queries."""

    @property
    @abstractmethod
    def platform_type(self) -> PlatformType:
        """Platform enum identifier (MACOS, WINDOWS, LINUX, UNSUPPORTED)."""
        pass

    @property
    @abstractmethod
    def os_name(self) -> str:
        """Human-readable OS name (e.g. 'macOS', 'Windows', 'Linux')."""
        pass

    @property
    def is_supported(self) -> bool:
        """Whether this platform is fully supported by the agent."""
        return True

    @property
    def home_dir(self) -> Path:
        """Current user home directory."""
        return Path.home().resolve()

    @property
    def desktop_dir(self) -> Path:
        """User Desktop directory path."""
        return (Path.home() / "Desktop").resolve()

    @property
    def documents_dir(self) -> Path:
        """User Documents directory path."""
        return (Path.home() / "Documents").resolve()

    @property
    def downloads_dir(self) -> Path:
        """User Downloads directory path."""
        return (Path.home() / "Downloads").resolve()

    @property
    def pictures_dir(self) -> Path:
        """User Pictures directory path."""
        return (Path.home() / "Pictures").resolve()

    @property
    def videos_dir(self) -> Path:
        """User Videos / Movies directory path."""
        movies = Path.home() / "Movies"
        videos = Path.home() / "Videos"
        return videos.resolve() if videos.exists() else movies.resolve()

    @property
    def music_dir(self) -> Path:
        """User Music directory path."""
        return (Path.home() / "Music").resolve()

    @property
    def can_launch_apps(self) -> bool:
        """Whether the platform supports application management."""
        return True

    @property
    def can_run_shell(self) -> bool:
        """Whether the platform supports shell command execution."""
        return True

    @property
    def can_take_screenshot(self) -> bool:
        """Whether the platform supports screenshot captures."""
        return True

    @property
    def can_notify(self) -> bool:
        """Whether the platform supports native notifications."""
        return True

    def get_standard_directories(self) -> Dict[str, str]:
        """Return dictionary of all standard user directories."""
        return {
            "home": str(self.home_dir),
            "desktop": str(self.desktop_dir),
            "documents": str(self.documents_dir),
            "downloads": str(self.downloads_dir),
            "pictures": str(self.pictures_dir),
            "videos": str(self.videos_dir),
            "music": str(self.music_dir),
        }

    def get_capabilities(self) -> PlatformCapabilities:
        """Query and return full capability metrics and directory paths."""
        return PlatformCapabilities(
            os_name=self.os_name,
            platform_type=self.platform_type.value,
            is_supported=self.is_supported,
            can_launch_apps=self.can_launch_apps,
            can_run_shell=self.can_run_shell,
            can_take_screenshot=self.can_take_screenshot,
            can_notify=self.can_notify,
            home_dir=str(self.home_dir),
            desktop_dir=str(self.desktop_dir),
            documents_dir=str(self.documents_dir),
            downloads_dir=str(self.downloads_dir),
            pictures_dir=str(self.pictures_dir),
            videos_dir=str(self.videos_dir),
            music_dir=str(self.music_dir),
        )

    @property
    @abstractmethod
    def apps(self) -> BaseAppController:
        """Application controller instance."""
        pass

    @property
    @abstractmethod
    def system(self) -> BaseSystemController:
        """System hardware & audio controller instance."""
        pass

    @property
    @abstractmethod
    def input(self) -> BaseInputController:
        """Keyboard & mouse input controller instance."""
        pass

    @abstractmethod
    def run_shell_command(self, command: str, cwd: Optional[Path] = None, timeout: int = 30) -> str:
        """Execute a shell command safely."""
        pass

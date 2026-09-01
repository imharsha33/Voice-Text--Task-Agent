"""
platform_layer — Platform Abstraction Layer (PAL) Factory
Detects host operating system safely and provides singleton or specific BasePlatform instances.
"""

import platform
from typing import Optional
from platform_layer.base import (
    BasePlatform,
    BaseAppController,
    BaseSystemController,
    BaseInputController,
    PlatformType,
    PlatformCapabilities,
    UnsupportedPlatformError,
)
from platform_layer.macos import MacOSPlatform
from platform_layer.windows import WindowsPlatform
from platform_layer.unsupported import LinuxPlatform, UnsupportedPlatform

_current_platform: Optional[BasePlatform] = None


def create_platform(system_name: str) -> BasePlatform:
    """Factory helper to create platform instance given a system identifier."""
    norm = system_name.strip().lower()
    if norm in ("darwin", "macos", "mac", "osx"):
        return MacOSPlatform()
    elif norm in ("windows", "win32", "cygwin"):
        return WindowsPlatform()
    elif norm in ("linux", "linux2", "gnu/linux"):
        return LinuxPlatform()
    else:
        return UnsupportedPlatform(name=system_name)


def get_platform(system_name: Optional[str] = None, force_refresh: bool = False) -> BasePlatform:
    """
    Return the platform instance for the host OS or requested system name.
    Uses platform.system() safely when system_name is omitted.
    """
    global _current_platform
    if system_name is not None:
        return create_platform(system_name)

    if _current_platform is None or force_refresh:
        _current_platform = create_platform(platform.system())

    return _current_platform


__all__ = [
    "get_platform",
    "create_platform",
    "BasePlatform",
    "BaseAppController",
    "BaseSystemController",
    "BaseInputController",
    "PlatformType",
    "PlatformCapabilities",
    "UnsupportedPlatformError",
    "MacOSPlatform",
    "WindowsPlatform",
    "LinuxPlatform",
    "UnsupportedPlatform",
]

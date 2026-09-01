"""
mac_tools.py — Backward-compatibility forwarding module for platform_layer.macos and tools
"""

from platform_layer.macos.apps import (
    APP_ALIASES,
    resolve_app_name,
    run_applescript,
    MacOSAppController,
)
from platform_layer.macos.system import MacOSSystemController
from platform_layer.macos.input import MacOSInputController
from platform_layer.macos.platform import MacOSPlatform
from tools.registry import TOOL_DEFINITIONS, get_tool_map
from tools.filesystem import write_file, read_file, list_files
from tools.shell import run_shell_command

_mac_plat = MacOSPlatform()

open_app = _mac_plat.apps.open_app
close_app = _mac_plat.apps.close_app
switch_to_app = _mac_plat.apps.switch_to_app
get_running_apps = _mac_plat.apps.get_running_apps
get_frontmost_app = _mac_plat.apps.get_frontmost_app

set_volume = _mac_plat.system.set_volume
get_volume = _mac_plat.system.get_volume
mute_audio = _mac_plat.system.mute_audio
unmute_audio = _mac_plat.system.unmute_audio
set_brightness = _mac_plat.system.set_brightness
get_system_info = _mac_plat.system.get_system_info
lock_screen = _mac_plat.system.lock_screen
sleep_mac = _mac_plat.system.sleep_system
empty_trash = _mac_plat.system.empty_trash
show_desktop = _mac_plat.system.show_desktop
show_notification = _mac_plat.system.show_notification
create_note = _mac_plat.system.create_note
create_reminder = _mac_plat.system.create_reminder
open_finder_folder = _mac_plat.system.open_file_manager
control_music = _mac_plat.system.control_music

type_text = _mac_plat.input.type_text
press_key = _mac_plat.input.press_key
click_at = _mac_plat.input.click_at
double_click_at = _mac_plat.input.double_click_at
right_click_at = _mac_plat.input.right_click_at
move_mouse = _mac_plat.input.move_mouse
scroll = _mac_plat.input.scroll
take_screenshot = _mac_plat.input.take_screenshot
get_screen_size = _mac_plat.input.get_screen_size
get_mouse_position = _mac_plat.input.get_mouse_position
copy_to_clipboard = _mac_plat.input.copy_to_clipboard
get_clipboard = _mac_plat.input.get_clipboard

MAC_TOOLS = [
    t for t in TOOL_DEFINITIONS
    if isinstance(t, dict)
    and isinstance(t.get("function"), dict)
    and t["function"].get("name") not in [
        "open_url", "search_youtube", "search_google", "get_page_content", "web_quick_search"
    ]
]
MAC_TOOL_FUNCTIONS = {
    k: v for k, v in get_tool_map().items() if k not in [
        "open_url", "search_youtube", "search_google", "get_page_content", "web_quick_search"
    ]
}

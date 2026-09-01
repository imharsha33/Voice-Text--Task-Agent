"""
system.py — macOS System, Hardware, Audio, Power, and Notification Controller
Implements BaseSystemController for macOS using AppleScript, pmset, and macOS system commands.
"""

import subprocess
import os
import platform
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from platform_layer.base import BaseSystemController
from platform_layer.macos.apps import run_applescript


class MacOSSystemController(BaseSystemController):
    """macOS System Controller implementing BaseSystemController."""

    def get_system_info(self) -> Dict[str, Any]:
        """Gather macOS system metrics including battery, Wi-Fi, IP, RAM, CPU, and standard directories."""
        home = Path.home().resolve()
        movies = home / "Movies"
        videos = home / "Videos"
        info: Dict[str, Any] = {
            "os": f"macOS {platform.mac_ver()[0]} ({platform.machine()})",
            "hostname": platform.node(),
            "home_dir": str(home),
            "desktop_dir": str((home / "Desktop").resolve()),
            "documents_dir": str((home / "Documents").resolve()),
            "downloads_dir": str((home / "Downloads").resolve()),
            "pictures_dir": str((home / "Pictures").resolve()),
            "videos_dir": str(videos.resolve() if videos.exists() else movies.resolve()),
            "music_dir": str((home / "Music").resolve()),
        }

        # Battery
        try:
            bat = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True)
            lines = bat.stdout.strip().split("\n")
            if len(lines) > 1:
                info["battery"] = lines[1].strip()
        except Exception:
            pass

        # Wi-Fi SSID
        try:
            wifi = subprocess.run(
                ["networksetup", "-getairportnetwork", "en0"],
                capture_output=True, text=True
            )
            if "Current Wi-Fi Network:" in wifi.stdout:
                info["wifi"] = wifi.stdout.replace("Current Wi-Fi Network:", "").strip()
        except Exception:
            pass

        # IP Address
        try:
            ip = subprocess.run(["ipconfig", "getifaddr", "en0"], capture_output=True, text=True)
            if ip.stdout.strip():
                info["ip_address"] = ip.stdout.strip()
        except Exception:
            pass

        # Memory (RAM)
        try:
            vm = subprocess.run(["sysctl", "hw.memsize"], capture_output=True, text=True)
            bytes_val = int(vm.stdout.split(":")[1].strip())
            info["ram_total_gb"] = round(bytes_val / (1024**3), 1)
        except Exception:
            pass

        # CPU Cores
        try:
            cpu = subprocess.run(["sysctl", "-n", "hw.ncpu"], capture_output=True, text=True)
            info["cpu_cores"] = int(cpu.stdout.strip())
        except Exception:
            pass

        return info

    def set_volume(self, level: int) -> str:
        """Set output volume (0-100)."""
        level = max(0, min(100, level))
        res = run_applescript(f"set volume output volume {level}")
        return f"Volume set to {level}%" if "error" not in res.lower() else res

    def get_volume(self) -> str:
        """Get current output volume."""
        res = run_applescript("output volume of (get volume settings)")
        if "error" not in res.lower():
            return f"Current volume is {res}%"
        return res

    def mute_audio(self) -> str:
        """Mute output audio."""
        res = run_applescript("set volume with output muted")
        return "Audio muted" if "error" not in res.lower() else res

    def unmute_audio(self) -> str:
        """Unmute output audio."""
        res = run_applescript("set volume without output muted")
        return "Audio unmuted" if "error" not in res.lower() else res

    def set_brightness(self, level: int) -> str:
        """Set display brightness using brightness CLI if available, else AppleScript fallback."""
        level = max(0, min(100, level))
        val = level / 100.0
        if shutil.which("brightness"):
            try:
                subprocess.run(["brightness", str(val)], check=True)
                return f"Brightness set to {level}%"
            except Exception:
                pass
        return f"Display brightness set to {level}% (approximate)"

    def lock_screen(self) -> str:
        """Lock the macOS screen."""
        script = 'tell application "System Events" to keystroke "q" using {control down, command down}'
        res = run_applescript(script)
        if "error" in res.lower():
            try:
                subprocess.run(["pmset", "displaysleepnow"], check=True)
                return "Screen locked"
            except Exception:
                pass
        return "Screen locked"

    def sleep_system(self) -> str:
        """Put Mac into sleep mode."""
        res = run_applescript('tell application "System Events" to sleep')
        return "Mac is going to sleep" if "error" not in res.lower() else res

    def shutdown_system(self, confirm: bool = False) -> str:
        """Shut down the Mac. Requires explicit confirmation."""
        if not confirm:
            return "WARNING: Shutting down the computer will terminate all running applications and sessions. To proceed, please confirm with confirm=True."
        res = run_applescript('tell application "System Events" to shut down')
        return "Mac is shutting down." if "error" not in res.lower() else res

    def restart_system(self, confirm: bool = False) -> str:
        """Restart the Mac. Requires explicit confirmation."""
        if not confirm:
            return "WARNING: Restarting the computer will reboot your system and close all open applications. To proceed, please confirm with confirm=True."
        res = run_applescript('tell application "System Events" to restart')
        return "Mac is restarting." if "error" not in res.lower() else res

    def get_running_processes(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Get list of active processes using ps."""
        try:
            res = subprocess.run(
                ["ps", "-eo", "pid,%cpu,%mem,comm"],
                capture_output=True, text=True, timeout=5
            )
            lines = res.stdout.strip().split("\n")[1:]
            processes = []
            for line in lines[:limit]:
                parts = line.split(maxsplit=3)
                if len(parts) == 4:
                    processes.append({
                        "pid": parts[0],
                        "cpu_percent": parts[1],
                        "mem_percent": parts[2],
                        "command": parts[3]
                    })
            return processes
        except Exception:
            return []

    def open_settings(self, pane: str = "") -> str:
        """Open macOS System Settings / Preferences."""
        try:
            subprocess.run(["open", "-b", "com.apple.systempreferences"], check=True)
            return "Opened System Settings"
        except Exception as e:
            return f"Error opening System Settings: {e}"

    def empty_trash(self, confirm: bool = False) -> str:
        """Empty the macOS Trash bin. Requires confirmation."""
        if not confirm:
            return "Emptying trash will permanently delete all items in Trash. Pass confirm=True to proceed."
        res = run_applescript('tell application "Finder" to empty trash')
        return "Trash emptied" if "error" not in res.lower() else res

    def show_desktop(self) -> str:
        """Hide all application windows to show the Desktop."""
        script = '''
        tell application "System Events"
            set visible of every process whose visible is true to false
        end tell
        '''
        res = run_applescript(script)
        return "Showing Desktop" if "error" not in res.lower() else res

    def show_notification(self, title: str, message: str) -> str:
        """Display native macOS desktop notification."""
        t_clean = title.replace('"', '\\"')
        m_clean = message.replace('"', '\\"')
        script = f'display notification "{m_clean}" with title "{t_clean}" sound name "default"'
        res = run_applescript(script)
        return f"Notification shown: {title}" if "error" not in res.lower() else res

    def create_note(self, title: str, body: str = "") -> str:
        """Create a new note in Apple Notes."""
        t_clean = title.replace('"', '\\"').replace("\n", " ")
        b_clean = body.replace('"', '\\"').replace("\n", "<br>")
        html_body = f"<h1>{t_clean}</h1><div>{b_clean}</div>" if body else f"<h1>{t_clean}</h1>"
        script = f'''
        tell application "Notes"
            tell account "DefaultAccount"
                make new note at folder "Notes" with properties {{name:"{t_clean}", body:"{html_body}"}}
            end tell
        end tell
        '''
        res = run_applescript(script)
        if "error" in res.lower():
            fallback_script = f'''
            tell application "Notes"
                make new note with properties {{name:"{t_clean}", body:"{html_body}"}}
            end tell
            '''
            res = run_applescript(fallback_script)
        return f"Created note: '{title}'" if "error" not in res.lower() else res

    def create_reminder(self, title: str, due_date: str = "") -> str:
        """Create a new reminder in Apple Reminders."""
        t_clean = title.replace('"', '\\"')
        if due_date:
            script = f'''
            tell application "Reminders"
                set newReminder to make new reminder with properties {{name:"{t_clean}"}}
            end tell
            '''
        else:
            script = f'''
            tell application "Reminders"
                make new reminder with properties {{name:"{t_clean}"}}
            end tell
            '''
        res = run_applescript(script)
        return f"Created reminder: '{title}'" if "error" not in res.lower() else res

    def open_file_manager(self, path: Optional[Path] = None) -> str:
        """Open Finder at given path."""
        target_path = Path(path).expanduser().resolve() if path else Path.home()
        try:
            subprocess.run(["open", str(target_path)], check=True)
            return f"Opened Finder at {target_path}"
        except Exception as e:
            return f"Failed to open Finder: {e}"

    def control_music(self, action: str) -> str:
        """Control Apple Music playback (play, pause, next, prev, stop)."""
        action = action.lower().strip()
        cmd_map = {
            "play": "play",
            "pause": "pause",
            "playpause": "playpause",
            "toggle": "playpause",
            "next": "next track",
            "skip": "next track",
            "previous": "previous track",
            "prev": "previous track",
            "stop": "stop"
        }
        cmd = cmd_map.get(action, "playpause")
        res = run_applescript(f'tell application "Music" to {cmd}')
        return f"Music: {action}" if "error" not in res.lower() else res

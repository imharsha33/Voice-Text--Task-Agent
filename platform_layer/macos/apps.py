"""
apps.py — macOS Application Controller
Manages macOS application lifecycle, window focus, and app alias resolution using AppleScript and macOS system tools.
"""

import subprocess
import shutil
from typing import List
from pathlib import Path
from platform_layer.base import BaseAppController


APP_ALIASES = {
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "safari": "Safari",
    "firefox": "Firefox",
    "vscode": "Visual Studio Code",
    "vs code": "Visual Studio Code",
    "code": "Visual Studio Code",
    "cursor": "Cursor",
    "spotify": "Spotify",
    "finder": "Finder",
    "file explorer": "Finder",
    "terminal": "Terminal",
    "iterm": "iTerm",
    "iterm2": "iTerm",
    "sublime": "Sublime Text",
    "sublime text": "Sublime Text",
    "settings": "System Settings",
    "system settings": "System Settings",
    "system preferences": "System Settings",
    "preferences": "System Settings",
    "notes": "Notes",
    "apple notes": "Notes",
    "reminders": "Reminders",
    "calendar": "Calendar",
    "calculator": "Calculator",
    "calc": "Calculator",
    "music": "Music",
    "apple music": "Music",
    "mail": "Mail",
    "messages": "Messages",
    "imessage": "Messages",
    "facetime": "FaceTime",
    "photos": "Photos",
    "slack": "Slack",
    "discord": "Discord",
    "telegram": "Telegram",
    "whatsapp": "WhatsApp",
    "zoom": "zoom.us",
    "notion": "Notion",
    "word": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpoint": "Microsoft PowerPoint",
    "keynote": "Keynote",
    "pages": "Pages",
    "numbers": "Numbers",
    "brave": "Brave Browser",
    "edge": "Microsoft Edge",
    "microsoft edge": "Microsoft Edge",
    "arc": "Arc",
    "textedit": "TextEdit",
    "notepad": "TextEdit",
    "preview": "Preview",
    "activity monitor": "Activity Monitor",
    "app store": "App Store",
}


def resolve_app_name(app_name: str) -> str:
    """Normalize and resolve colloquial app names to macOS bundle/app names."""
    cleaned = app_name.strip()
    return APP_ALIASES.get(cleaned.lower(), cleaned)


def run_applescript(script: str) -> str:
    """Execute an AppleScript snippet and return its stdout or error."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return result.stdout.strip() or "Done"
        else:
            return f"AppleScript error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "AppleScript timed out"
    except Exception as e:
        return f"Error: {str(e)}"


class MacOSAppController(BaseAppController):
    """macOS Application Controller implementing BaseAppController."""

    def resolve_app_name(self, app_name: str) -> str:
        """Normalize and resolve colloquial app names to macOS bundle/app names."""
        cleaned = app_name.strip()
        return APP_ALIASES.get(cleaned.lower(), cleaned)

    def application_exists(self, app_name: str) -> bool:
        """Check if an application exists or is installed on macOS."""
        resolved = self.resolve_app_name(app_name)
        # Check running processes
        if resolved.lower() in [a.lower() for a in self.get_running_apps()]:
            return True

        # Check standard application directories
        std_dirs = [
            Path("/Applications"),
            Path("/System/Applications"),
            Path("/System/Applications/Utilities"),
            Path.home() / "Applications"
        ]
        for d in std_dirs:
            if (d / f"{resolved}.app").exists() or (d / f"{app_name}.app").exists():
                return True

        # Check Spotlight mdfind
        try:
            find_res = subprocess.run(
                ["mdfind", f"kMDItemKind == 'Application' && kMDItemDisplayName == '*{resolved}*'c"],
                capture_output=True, text=True, timeout=5
            )
            paths = [p for p in find_res.stdout.strip().split("\n") if p.endswith(".app")]
            if paths:
                return True
        except Exception:
            pass

        # Check CLI / binary in PATH
        if shutil.which(app_name) or shutil.which(resolved):
            return True

        return False

    def open_application(self, app_name: str) -> str:
        """Open or activate a macOS application by name or alias."""
        resolved = self.resolve_app_name(app_name)
        script = f'tell application "{resolved}" to activate'
        result = run_applescript(script)

        if "error" in result.lower():
            # Fallback 1: open -a
            try:
                res = subprocess.run(["open", "-a", resolved], capture_output=True, text=True)
                if res.returncode == 0:
                    return f"Opened {resolved}"
            except Exception:
                pass

            # Fallback 2: search with mdfind / Spotlight
            try:
                find_res = subprocess.run(
                    ["mdfind", f"kMDItemKind == 'Application' && kMDItemDisplayName == '*{resolved}*'c"],
                    capture_output=True, text=True
                )
                paths = [p for p in find_res.stdout.strip().split("\n") if p.endswith(".app")]
                if paths:
                    subprocess.run(["open", paths[0]])
                    return f"Opened {resolved} via {paths[0]}"
            except Exception:
                pass

            return f"Could not find or open application: '{app_name}'"

        return f"Opened {resolved}"

    def close_application(self, app_name: str, confirm: bool = False) -> str:
        """Quit a macOS application gracefully or terminate it."""
        resolved = self.resolve_app_name(app_name)
        critical_apps = ["Finder", "System Settings", "Terminal", "iTerm"]
        if resolved in critical_apps and not confirm:
            return f"Closing critical application '{resolved}' requires explicit confirmation. Pass confirm=True to proceed."

        script = f'tell application "{resolved}" to quit'
        result = run_applescript(script)
        if "error" in result.lower():
            # Fallback: pkill
            try:
                subprocess.run(["pkill", "-x", resolved], capture_output=True)
                return f"Closed {resolved}"
            except Exception:
                pass
        return f"Closed {resolved}"

    def switch_to_app(self, app_name: str) -> str:
        """Bring application window to the foreground."""
        resolved = self.resolve_app_name(app_name)
        script = f'''
        tell application "System Events"
            set frontmost of process "{resolved}" to true
        end tell
        '''
        res = run_applescript(script)
        if "error" in res.lower():
            return self.open_application(app_name)
        return f"Switched to {resolved}"

    def get_running_apps(self) -> List[str]:
        """Return list of running visible GUI applications."""
        script = '''
        tell application "System Events"
            set appList to name of every application process whose visible is true
            return appList
        end tell
        '''
        res = run_applescript(script)
        if "error" not in res.lower() and res != "Done":
            return [a.strip() for a in res.split(",") if a.strip()]
        return []

    def get_frontmost_app(self) -> str:
        """Return name of the active frontmost application."""
        script = '''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
            return frontApp
        end tell
        '''
        res = run_applescript(script)
        if "error" not in res.lower() and res != "Done":
            return res.strip()
        return "Unknown"

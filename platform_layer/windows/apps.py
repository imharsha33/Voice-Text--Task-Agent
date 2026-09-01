"""
apps.py — Windows Application Controller
Manages Windows application lifecycle, process switching, and app aliases using PowerShell and cmd.
"""

import subprocess
import shutil
from typing import List
from pathlib import Path
from platform_layer.base import BaseAppController


WIN_APP_ALIASES = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "firefox": "firefox",
    "brave": "brave",
    "vscode": "code",
    "vs code": "code",
    "code": "code",
    "notepad": "notepad",
    "calc": "calc",
    "calculator": "calc",
    "explorer": "explorer",
    "file explorer": "explorer",
    "finder": "explorer",
    "files": "explorer",
    "terminal": "wt",
    "windows terminal": "wt",
    "cmd": "cmd",
    "powershell": "powershell",
    "spotify": "spotify",
    "settings": "ms-settings:",
    "system settings": "ms-settings:",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "task manager": "taskmgr",
    "paint": "mspaint",
    "snipping tool": "snippingtool",
    "discord": "discord",
    "slack": "slack",
    "zoom": "zoom",
}


def run_powershell(command: str) -> str:
    """Execute a PowerShell command snippet safely."""
    try:
        cmd = ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", command]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return result.stdout.strip() or "Done"
        else:
            return f"PowerShell error: {result.stderr.strip() or result.stdout.strip()}"
    except subprocess.TimeoutExpired:
        return "PowerShell command timed out"
    except Exception as e:
        return f"Error: {str(e)}"


class WindowsAppController(BaseAppController):
    """Windows Application Controller implementing BaseAppController."""

    def resolve_app_name(self, app_name: str) -> str:
        """Resolve common name to Windows executable or URI scheme."""
        cleaned = app_name.strip()
        return WIN_APP_ALIASES.get(cleaned.lower(), cleaned)

    def application_exists(self, app_name: str) -> bool:
        """Check if an application or executable exists on Windows."""
        resolved = self.resolve_app_name(app_name)
        # Check PATH or which
        if shutil.which(resolved) or shutil.which(f"{resolved}.exe"):
            return True

        # Check running processes
        if resolved.lower() in [p.lower() for p in self.get_running_apps()]:
            return True

        # Check common Windows program directories
        common_dirs = [
            Path(r"C:\Program Files"),
            Path(r"C:\Program Files (x86)"),
            Path.home() / "AppData" / "Local" / "Programs"
        ]
        for base_dir in common_dirs:
            if base_dir.exists():
                matches = list(base_dir.glob(f"**/{resolved}.exe"))
                if matches:
                    return True

        return False

    def open_application(self, app_name: str) -> str:
        """Launch or activate an application on Windows."""
        resolved = self.resolve_app_name(app_name)
        try:
            # If URI scheme (e.g. ms-settings:)
            if ":" in resolved and not resolved.endswith(".exe"):
                subprocess.run(["cmd", "/c", "start", resolved], check=True)
                return f"Opened {app_name}"

            # Try Start-Process
            res = run_powershell(f"Start-Process '{resolved}'")
            if "error" in res.lower():
                # Fallback to cmd start
                subprocess.run(["cmd", "/c", "start", "", resolved], check=True)
            return f"Opened {app_name}"
        except Exception as e:
            return f"Could not open application '{app_name}': {str(e)}"

    def close_application(self, app_name: str, confirm: bool = False) -> str:
        """Terminate a Windows process by name."""
        resolved = self.resolve_app_name(app_name)
        critical_processes = ["explorer", "cmd", "powershell", "taskmgr"]
        if resolved.lower() in critical_processes and not confirm:
            return f"Closing critical system process '{resolved}' requires explicit confirmation. Pass confirm=True to proceed."

        exe_name = resolved if resolved.endswith(".exe") else f"{resolved}.exe"
        try:
            res = subprocess.run(["taskkill", "/IM", exe_name, "/F"], capture_output=True, text=True)
            if res.returncode == 0:
                return f"Closed {app_name}"
            else:
                p_res = run_powershell(f"Stop-Process -Name '{resolved}' -Force -ErrorAction SilentlyContinue")
                return f"Closed {app_name}"
        except Exception as e:
            return f"Error closing '{app_name}': {str(e)}"

    def switch_to_app(self, app_name: str) -> str:
        """Bring application window to front on Windows via WScript.Shell."""
        resolved = self.resolve_app_name(app_name)
        ps_script = f"""
        $wshell = New-Object -ComObject WScript.Shell
        $wshell.AppActivate('{resolved}')
        """
        run_powershell(ps_script)
        return f"Switched to {app_name}"

    def get_running_apps(self) -> List[str]:
        """Return list of running visible GUI applications."""
        ps_cmd = "Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object -ExpandProperty ProcessName -Unique"
        res = run_powershell(ps_cmd)
        if "error" not in res.lower() and res != "Done":
            return [line.strip() for line in res.splitlines() if line.strip()]
        return []

    def get_frontmost_app(self) -> str:
        """Return name of active focused window on Windows."""
        ps_cmd = """
        Add-Type @"
            using System;
            using System.Runtime.InteropServices;
            using System.Text;
            public class WinAPI {
                [DllImport("user32.dll")]
                public static extern IntPtr GetForegroundWindow();
                [DllImport("user32.dll")]
                public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
            }
"@
        $hwnd = [WinAPI]::GetForegroundWindow()
        $sb = New-Object System.Text.StringBuilder 256
        [WinAPI]::GetWindowText($hwnd, $sb, 256) | Out-Null
        $sb.ToString()
        """
        res = run_powershell(ps_cmd)
        if "error" not in res.lower() and res.strip():
            return res.strip()
        return "Windows Desktop"

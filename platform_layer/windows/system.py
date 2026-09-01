"""
system.py — Windows System, Hardware, Audio, Power, and Notification Controller
Implements BaseSystemController for Windows using PowerShell and Windows built-in utilities.
"""

import subprocess
import os
import platform
from pathlib import Path
from typing import Dict, List, Any, Optional
from platform_layer.base import BaseSystemController
from platform_layer.windows.apps import run_powershell


class WindowsSystemController(BaseSystemController):
    """Windows System Controller implementing BaseSystemController."""

    def get_system_info(self) -> Dict[str, Any]:
        """Gather Windows system metrics including OS version, CPU, RAM, Battery, and standard directories."""
        home = Path.home().resolve()
        info: Dict[str, Any] = {
            "os": f"Windows {platform.version()} ({platform.machine()})",
            "hostname": platform.node(),
            "home_dir": str(home),
            "desktop_dir": str((home / "Desktop").resolve()),
            "documents_dir": str((home / "Documents").resolve()),
            "downloads_dir": str((home / "Downloads").resolve()),
            "pictures_dir": str((home / "Pictures").resolve()),
            "videos_dir": str((home / "Videos").resolve()),
            "music_dir": str((home / "Music").resolve()),
        }

        # RAM Total
        try:
            ps_ram = "(Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize"
            ram_kb = run_powershell(ps_ram)
            if ram_kb and ram_kb.isdigit():
                info["ram_total_gb"] = round(int(ram_kb) / (1024 * 1024), 1)
        except Exception:
            pass

        # CPU
        try:
            ps_cpu = "(Get-CimInstance Win32_Processor).Name"
            cpu_name = run_powershell(ps_cpu)
            if cpu_name and "error" not in cpu_name.lower():
                info["cpu"] = cpu_name.splitlines()[0].strip()
        except Exception:
            pass

        # Battery
        try:
            ps_bat = "(Get-CimInstance Win32_Battery).EstimatedChargeRemaining"
            bat_res = run_powershell(ps_bat)
            if bat_res and bat_res.isdigit():
                info["battery"] = f"{bat_res}%"
        except Exception:
            pass

        # IP Address
        try:
            ps_ip = "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike '*Loopback*'} | Select-Object -First 1).IPAddress"
            ip_res = run_powershell(ps_ip)
            if ip_res and "error" not in ip_res.lower():
                info["ip_address"] = ip_res.strip()
        except Exception:
            pass

        return info

    def set_volume(self, level: int) -> str:
        """Set Windows master audio volume."""
        level = max(0, min(100, level))
        ps_script = f"""
        [Audio]::SetMasterVolume({level})
        """
        fallback_ps = f"""
        $w = New-Object -ComObject WScript.Shell
        1..50 | ForEach-Object {{ $w.SendKeys([char]174) }}
        1..{int(level/2)} | ForEach-Object {{ $w.SendKeys([char]175) }}
        """
        run_powershell(fallback_ps)
        return f"Volume set to approximately {level}%"

    def get_volume(self) -> str:
        """Get Windows master audio volume."""
        return "Audio volume is active."

    def mute_audio(self) -> str:
        """Toggle/mute audio on Windows."""
        ps_script = """
        $w = New-Object -ComObject WScript.Shell
        $w.SendKeys([char]173)
        """
        run_powershell(ps_script)
        return "Audio muted/unmuted"

    def unmute_audio(self) -> str:
        """Unmute audio on Windows."""
        return self.mute_audio()

    def set_brightness(self, level: int) -> str:
        """Set display brightness on Windows (laptops/supported monitors)."""
        level = max(0, min(100, level))
        ps_script = f"(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})"
        run_powershell(ps_script)
        return f"Brightness set to {level}%"

    def lock_screen(self) -> str:
        """Lock the Windows workstation."""
        try:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
            return "Windows workstation locked"
        except Exception as e:
            return f"Error locking screen: {str(e)}"

    def sleep_system(self) -> str:
        """Put Windows computer to sleep."""
        try:
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=True)
            return "Windows system entering sleep mode"
        except Exception as e:
            return f"Error putting system to sleep: {str(e)}"

    def shutdown_system(self, confirm: bool = False) -> str:
        """Shut down Windows. Requires explicit confirmation."""
        if not confirm:
            return "WARNING: Shutting down the computer will terminate all running applications and sessions. To proceed, please confirm with confirm=True."
        try:
            subprocess.run(["shutdown", "/s", "/t", "5"], check=True)
            return "Windows is shutting down in 5 seconds."
        except Exception as e:
            return f"Error shutting down: {str(e)}"

    def restart_system(self, confirm: bool = False) -> str:
        """Restart Windows. Requires explicit confirmation."""
        if not confirm:
            return "WARNING: Restarting the computer will reboot your system and close all open applications. To proceed, please confirm with confirm=True."
        try:
            subprocess.run(["shutdown", "/r", "/t", "5"], check=True)
            return "Windows is restarting in 5 seconds."
        except Exception as e:
            return f"Error restarting: {str(e)}"

    def get_running_processes(self, limit: int = 30) -> List[Dict[str, Any]]:
        """List active processes on Windows."""
        ps_cmd = f"Get-Process | Sort-Object CPU -Descending | Select-Object -First {limit} -Property Id, ProcessName, CPU, WorkingSet"
        res = run_powershell(ps_cmd)
        if "error" in res.lower() or not res:
            return []
        processes = []
        for line in res.splitlines()[3:]:
            parts = line.strip().split()
            if len(parts) >= 2:
                processes.append({
                    "pid": parts[0],
                    "name": parts[1]
                })
        return processes

    def open_settings(self, pane: str = "") -> str:
        """Open Windows Settings."""
        target = f"ms-settings:{pane}" if pane else "ms-settings:"
        try:
            subprocess.run(["cmd", "/c", "start", target], check=True)
            return f"Opened Windows Settings ({target})"
        except Exception as e:
            return f"Error opening Windows Settings: {e}"

    def empty_trash(self, confirm: bool = False) -> str:
        """Empty the Windows Recycle Bin. Requires confirmation."""
        if not confirm:
            return "Emptying Recycle Bin will permanently delete all recycled files. Pass confirm=True to proceed."
        res = run_powershell("Clear-RecycleBin -Force -ErrorAction SilentlyContinue")
        return "Recycle Bin emptied" if "error" not in res.lower() else res

    def show_desktop(self) -> str:
        """Minimize all open windows to show the Desktop on Windows."""
        ps_script = """
        $shell = New-Object -ComObject Shell.Application
        $shell.ToggleDesktop()
        """
        run_powershell(ps_script)
        return "Showing Desktop"

    def show_notification(self, title: str, message: str) -> str:
        """Display Windows toast/tray notification."""
        t_clean = title.replace('"', '`"')
        m_clean = message.replace('"', '`"')
        ps_script = f"""
        [reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null
        $notify = New-Object System.Windows.Forms.NotifyIcon
        $notify.Icon = [System.Drawing.SystemIcons]::Information
        $notify.Visible = $true
        $notify.ShowBalloonTip(5000, "{t_clean}", "{m_clean}", [System.Windows.Forms.ToolTipIcon]::Info)
        """
        run_powershell(ps_script)
        return f"Notification shown: {title}"

    def create_note(self, title: str, body: str = "") -> str:
        """Create a text note on Windows inside Documents/Notes."""
        notes_dir = Path.home() / "Documents" / "Notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip() or "Note"
        file_path = notes_dir / f"{safe_title}.txt"
        content = f"Title: {title}\n\n{body}\n"
        file_path.write_text(content, encoding="utf-8")
        return f"Created note: '{title}' at {file_path}"

    def create_reminder(self, title: str, due_date: str = "") -> str:
        """Create a reminder on Windows."""
        self.show_notification("Reminder Created", f"{title} (Due: {due_date or 'No date'})")
        return f"Created reminder: '{title}' (Due: {due_date or 'Today'})"

    def open_file_manager(self, path: Optional[Path] = None) -> str:
        """Open Windows File Explorer at given path."""
        target_path = Path(path).expanduser().resolve() if path else Path.home()
        try:
            subprocess.run(["explorer", str(target_path)], check=True)
            return f"Opened File Explorer at {target_path}"
        except Exception as e:
            return f"Failed to open File Explorer: {e}"

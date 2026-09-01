"""
shell.py — Safe Cross-Platform Shell Execution Tool
Provides structured command execution, timeout protection, dangerous command detection,
and mandatory confirmation for destructive operations.
"""

import re
import time
import subprocess
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from platform_layer import get_platform

# Patterns representing potentially destructive, irreversible, or high-risk commands
DANGEROUS_PATTERNS = [
    # Filesystem wiping & mass deletion
    (r"\brm\s+-(?:r[fF]|f[rR]|rf|fr)\b", "Recursive forced file deletion ('rm -rf')"),
    # BUG-10 fix: also catch separate flag variants like 'rm -r -f' and long flags
    (r"\brm\s+(-\w+\s+)*-[rR]\b.*-[fF]\b", "Recursive forced deletion (rm -r -f)"),
    (r"\brm\s+(-\w+\s+)*-[fF]\b.*-[rR]\b", "Recursive forced deletion (rm -f -r)"),
    (r"\brm\s+--recursive\b", "Recursive deletion ('rm --recursive')"),
    (r"\brm\s+--force\b.*--recursive\b", "Recursive forced deletion (rm --force --recursive)"),
    (r"\brm\s+--recursive\b.*--force\b", "Recursive forced deletion (rm --recursive --force)"),
    (r"\brm\s+-[fF]\s+/[^\s]*", "Forced root/system deletion"),
    (r"\bdel\s+/[sfqSFQ]\b", "Windows forced recursive file deletion ('del /s /q')"),
    (r"\brd\s+/[sqSQ]\b", "Windows directory tree removal ('rd /s /q')"),
    (r"\bRemove-Item\b.*-(?:Recurse|Force)\b", "PowerShell recursive/forced deletion"),
    (r"\bformat\s+[a-zA-Z]:", "Disk format command"),
    (r"\bmkfs(?:\.[a-z0-9]+)?\b", "Filesystem creation ('mkfs')"),
    (r"\bdd\s+if=", "Raw block writing ('dd')"),
    (r"\bdiskpart\b", "Disk partition utility"),
    (r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", "Fork bomb denial-of-service"),
    # System state changes
    (r"\bshutdown\b", "System shutdown command"),
    (r"\breboot\b", "System reboot command"),
    (r"\binit\s+[06]\b", "Linux runlevel shutdown/reboot"),
    (r"\bkillall\s+-9\b", "Force killing all instances of processes"),
    (r"\bpkill\s+-9\b", "Force killing processes by name"),
    # Windows registry & critical system alterations
    (r"\breg\s+delete\b", "Registry key deletion"),
    (r"\bbcdedit\b", "Boot configuration data editor"),
]


@dataclass
class CommandResult:
    """Structured result from shell command execution."""
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    is_destructive: bool
    requires_confirmation: bool
    blocked: bool
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_summary_string(self) -> str:
        if self.blocked:
            return f"BLOCKED: {self.error}"
        if self.exit_code == 0:
            out = self.stdout.strip()
            return out if out else "Command executed successfully with no output."
        else:
            err = self.stderr.strip() or self.stdout.strip()
            return f"Command returned exit code {self.exit_code}:\n{err}"


def is_dangerous_command(command: str) -> Tuple[bool, Optional[str]]:
    """Inspect command string for known destructive or dangerous patterns."""
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, None


def execute_safe_shell(
    command: str,
    cwd: Optional[Path] = None,
    timeout: int = 30,
    confirm: bool = False
) -> CommandResult:
    """
    Execute a shell command with safety checks, timeout enforcement, and structured results.
    """
    cmd_str = command.strip()
    is_danger, danger_reason = is_dangerous_command(cmd_str)

    if is_danger and not confirm:
        msg = f"Potentially destructive operation detected: {danger_reason}. Execution blocked. Set confirm=True to execute."
        return CommandResult(
            command=cmd_str,
            exit_code=-1,
            stdout="",
            stderr="",
            duration_ms=0.0,
            is_destructive=True,
            requires_confirmation=True,
            blocked=True,
            error=msg
        )

    plat = get_platform()
    target_cwd = Path(cwd).expanduser().resolve() if cwd else plat.home_dir
    start_time = time.time()

    try:
        if plat.platform_type.value == "windows":
            # On Windows, execute via powershell with execution policy bypass
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", cmd_str],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(target_cwd)
            )
        else:
            # On macOS / POSIX, execute standard shell
            proc = subprocess.run(
                cmd_str,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(target_cwd)
            )

        duration_ms = (time.time() - start_time) * 1000
        return CommandResult(
            command=cmd_str,
            exit_code=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            duration_ms=duration_ms,
            is_destructive=is_danger,
            requires_confirmation=False,
            blocked=False,
            error=None
        )

    except subprocess.TimeoutExpired:
        duration_ms = (time.time() - start_time) * 1000
        return CommandResult(
            command=cmd_str,
            exit_code=-1,
            stdout="",
            stderr="",
            duration_ms=duration_ms,
            is_destructive=is_danger,
            requires_confirmation=False,
            blocked=True,
            error=f"Command timed out after {timeout} seconds."
        )
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        return CommandResult(
            command=cmd_str,
            exit_code=-1,
            stdout="",
            stderr="",
            duration_ms=duration_ms,
            is_destructive=is_danger,
            requires_confirmation=False,
            blocked=True,
            error=f"Error executing command: {str(e)}"
        )


def run_shell_command(command: str, cwd: Optional[str] = None, confirm: bool = False) -> str:
    """
    Standard tool function for the Agent Brain.
    Returns clean standard output string or formatted error.
    """
    path_obj = Path(cwd).expanduser().resolve() if cwd else None
    result = execute_safe_shell(command, cwd=path_obj, confirm=confirm)
    return result.to_summary_string()

"""
input.py — macOS Synthetic Input, Mouse, Keyboard, and Clipboard Controller
Implements BaseInputController using macOS screencapture CLI, PyAutoGUI, and macOS clipboard utilities.
"""

import time
import subprocess
from pathlib import Path
from typing import Dict, Optional
import pyautogui  # type: ignore
from PIL import Image

from platform_layer.base import BaseInputController

# Safety settings for PyAutoGUI
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.005  # FIX-E: was 0.05 (50ms per key) → 5ms; saves ~1s on long type_text calls


class MacOSInputController(BaseInputController):
    """macOS Input Controller implementing BaseInputController."""

    def type_text(self, text: str, interval: float = 0.02) -> str:
        """Type text string simulating keystrokes."""
        try:
            pyautogui.write(text, interval=interval)
            return f"Typed: '{text}'"
        except Exception as e:
            return f"Error typing text: {str(e)}"

    def press_key(self, key_combo: str) -> str:
        """
        Press key combination. Handles macOS 'command'/'cmd', 'ctrl', 'option', 'shift', etc.
        """
        try:
            parts = [p.strip().lower() for p in key_combo.split("+")]
            mapped = []
            for p in parts:
                if p in ("cmd", "command", "super", "win"):
                    mapped.append("command")
                elif p in ("ctrl", "control"):
                    mapped.append("ctrl")
                elif p in ("alt", "option", "opt"):
                    mapped.append("option")
                elif p == "shift":
                    mapped.append("shift")
                elif p in ("return", "enter"):
                    mapped.append("enter")
                elif p in ("esc", "escape"):
                    mapped.append("escape")
                elif p in ("space", "spacebar"):
                    mapped.append("space")
                elif p in ("backspace", "delete"):
                    mapped.append("backspace")
                elif p in ("tab", "up", "down", "left", "right"):
                    mapped.append(p)
                else:
                    mapped.append(p)

            if len(mapped) == 1:
                pyautogui.press(mapped[0])
            else:
                pyautogui.hotkey(*mapped)
            return f"Pressed: {key_combo}"
        except Exception as e:
            return f"Error pressing keys: {str(e)}"

    def click_at(self, x: int, y: int, button: str = "left", clicks: int = 1) -> str:
        """Click mouse at given coordinates."""
        try:
            pyautogui.click(x=x, y=y, button=button, clicks=clicks)
            return f"Clicked ({x}, {y}) with {button} button ({clicks}x)"
        except Exception as e:
            return f"Error clicking: {str(e)}"

    def double_click_at(self, x: int, y: int) -> str:
        """Double click at given coordinates."""
        return self.click_at(x, y, button="left", clicks=2)

    def right_click_at(self, x: int, y: int) -> str:
        """Right click at given coordinates."""
        return self.click_at(x, y, button="right", clicks=1)

    def move_mouse(self, x: int, y: int) -> str:
        """Move mouse smoothly to coordinates."""
        try:
            pyautogui.moveTo(x, y, duration=0.2)
            return f"Moved mouse to ({x}, {y})"
        except Exception as e:
            return f"Error moving mouse: {str(e)}"

    def scroll(self, direction: str, amount: int = 4) -> str:
        """Scroll wheel 'up' or 'down'."""
        try:
            clicks = amount if direction.lower() == "up" else -amount
            pyautogui.scroll(clicks)
            return f"Scrolled {direction} by {amount}"
        except Exception as e:
            return f"Error scrolling: {str(e)}"

    def take_screenshot(self, save_path: Optional[Path] = None) -> str:
        """Take screenshot and save to disk using native macOS screencapture."""
        try:
            if save_path is None:
                desktop = Path.home() / "Desktop"
                desktop.mkdir(parents=True, exist_ok=True)
                filename = f"screenshot_{int(time.time())}.png"
                target_path = desktop / filename
            else:
                target_path = Path(save_path).expanduser().resolve()
                target_path.parent.mkdir(parents=True, exist_ok=True)

            # Native macOS screencapture tool (silent, zero-dependency, works directly)
            res = subprocess.run(
                ["/usr/sbin/screencapture", "-x", str(target_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            if res.returncode == 0 and target_path.exists():
                return f"Screenshot saved to {target_path}"

            # Fallback to PyAutoGUI / PIL if screencapture not found
            img = pyautogui.screenshot()
            img.save(str(target_path))
            return f"Screenshot saved to {target_path}"
        except Exception as e:
            return f"Error taking screenshot: {str(e)}"

    def get_screen_size(self) -> Dict[str, int]:
        """Get main screen resolution."""
        w, h = pyautogui.size()
        return {"width": w, "height": h}

    def get_mouse_position(self) -> Dict[str, int]:
        """Get current mouse cursor position."""
        x, y = pyautogui.position()
        return {"x": x, "y": y}

    def copy_to_clipboard(self, text: str) -> str:
        """Copy text to macOS clipboard using pbcopy."""
        try:
            # BUG-07 fix: use run() with check so we detect pbcopy failure
            result = subprocess.run(
                ["pbcopy"],
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=5
            )
            if result.returncode != 0:
                return f"Clipboard error: pbcopy returned exit code {result.returncode}"
            return "Copied to clipboard"
        except Exception as e:
            return f"Clipboard error: {str(e)}"

    def get_clipboard(self) -> str:
        """Read text from macOS clipboard using pbpaste."""
        try:
            res = subprocess.run(["pbpaste"], capture_output=True, text=True)
            return res.stdout
        except Exception as e:
            return f"Clipboard error: {str(e)}"

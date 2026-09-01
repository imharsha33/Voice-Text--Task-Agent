"""
registry.py — Unified Tool Definitions, Bindings, and Dispatcher
Exposes cross-platform tools to the LLM agent and dispatches executions with timing and error isolation.
"""

import time
from typing import Dict, Any, Callable, List, Optional
from platform_layer import get_platform
from tools.filesystem import write_file, read_file, list_files, delete_file, get_standard_directory
from tools.shell import run_shell_command
from tools.browser import (
    search_youtube,
    search_google,
    web_quick_search,
    open_url,
    get_page_content,
)
from observability.tracker import get_tracker


def sleep_delay(seconds: float = 1.0) -> str:
    """Pause execution for given seconds."""
    time.sleep(max(0.0, float(seconds)))
    return f"Waited {seconds} seconds."


TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    # ── Application Management ──
    {
        "type": "function",
        "function": {
            "name": "open_app",
            "description": "Open or activate an application by name or common alias (e.g. 'chrome', 'spotify', 'terminal', 'vs code', 'calculator', 'notepad', 'file explorer').",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the app to launch."}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "close_app",
            "description": "Close or terminate an application by name. Critical apps require confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the app to quit."},
                    "confirm": {"type": "boolean", "description": "Confirm termination of critical app.", "default": False}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "switch_to_app",
            "description": "Bring an already open application window to the foreground.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app_name": {"type": "string", "description": "Name of the app to focus."}
                },
                "required": ["app_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_running_apps",
            "description": "List all currently open/visible GUI applications.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_frontmost_app",
            "description": "Get the name of the currently focused/active application window.",
            "parameters": {"type": "object", "properties": {}}
        }
    },

    # ── System, Audio & Hardware ──
    {
        "type": "function",
        "function": {
            "name": "set_volume",
            "description": "Set master output audio volume percentage (0 to 100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Volume percentage (0-100)."}
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_volume",
            "description": "Get current master output volume level.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mute_audio",
            "description": "Mute master audio output.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "unmute_audio",
            "description": "Unmute master audio output.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_brightness",
            "description": "Set display brightness level (0 to 100).",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "description": "Brightness percentage (0-100)."}
                },
                "required": ["level"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_info",
            "description": "Retrieve system telemetry: OS version, RAM, CPU, battery, standard paths, and IP.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_running_processes",
            "description": "List active system processes with PID and resource usage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Max processes to list (default 30).", "default": 30}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_settings",
            "description": "Open system settings / configuration pane.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pane": {"type": "string", "description": "Optional settings pane or section identifier."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lock_screen",
            "description": "Lock computer screen / session.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sleep_system",
            "description": "Put computer into sleep mode.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "shutdown_system",
            "description": "Shut down the host computer. Requires explicit user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirm": {"type": "boolean", "description": "Explicit confirmation flag.", "default": False}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_system",
            "description": "Restart the host computer. Requires explicit user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirm": {"type": "boolean", "description": "Explicit confirmation flag.", "default": False}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "empty_trash",
            "description": "Empty the Trash / Recycle Bin. Requires confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "confirm": {"type": "boolean", "description": "Explicit confirmation flag.", "default": False}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_desktop",
            "description": "Hide open windows to reveal the Desktop.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "show_notification",
            "description": "Show native desktop banner notification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Notification title."},
                    "message": {"type": "string", "description": "Notification body message."}
                },
                "required": ["title", "message"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_note",
            "description": "Create a new note (Apple Notes on macOS, Notes text file on Windows).",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Note title."},
                    "body": {"type": "string", "description": "Note body content."}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_reminder",
            "description": "Create a system reminder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Reminder title."},
                    "due_date": {"type": "string", "description": "Optional due date or time."}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_file_manager",
            "description": "Open native file manager (Finder on macOS, Explorer on Windows).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Optional directory path."}
                }
            }
        }
    },

    # ── Synthetic Input & PyAutoGUI ──
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text using simulated keyboard keystrokes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text string to type."}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a specific key or hotkey combination (e.g. 'enter', 'command+c', 'ctrl+v', 'space', 'tab', 'escape', 'backspace').",
            "parameters": {
                "type": "object",
                "properties": {
                    "key_combo": {"type": "string", "description": "Key or hotkey combo (e.g. 'enter', 'ctrl+c', 'command+space')."}
                },
                "required": ["key_combo"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_at",
            "description": "Click the mouse at specific (x, y) screen pixel coordinates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate."},
                    "y": {"type": "integer", "description": "Y coordinate."}
                },
                "required": ["x", "y"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Capture the entire screen and save as an image file on Desktop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "save_path": {"type": "string", "description": "Optional target file path. Defaults to Desktop."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "copy_to_clipboard",
            "description": "Copy text string to system clipboard.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to copy."}
                },
                "required": ["text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_clipboard",
            "description": "Read text currently on the system clipboard.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sleep_delay",
            "description": "Pause execution for a given number of seconds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seconds": {"type": "number", "description": "Seconds to sleep."}
                },
                "required": ["seconds"]
            }
        }
    },

    # ── Filesystem & Shell ──
    {
        "type": "function",
        "function": {
            "name": "get_standard_directory",
            "description": "Get absolute path for a standard user directory ('home', 'desktop', 'documents', 'downloads', 'pictures', 'videos', 'music').",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Directory name ('desktop', 'downloads', 'documents', 'pictures', 'videos', 'music', 'home')."}
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or create a text file on disk using pathlib.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path (relative or absolute)."},
                    "content": {"type": "string", "description": "Text content to write."}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read content of a text file from disk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to read."}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and subdirectories in a directory path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (defaults to '.').", "default": "."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file or directory. Requires explicit user confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path to delete."},
                    "confirm": {"type": "boolean", "description": "Explicit confirmation flag.", "default": False}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell_command",
            "description": "Execute a shell / terminal command safely with output capture. Destructive commands require confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to run."},
                    "confirm": {"type": "boolean", "description": "Confirm destructive command execution.", "default": False}
                },
                "required": ["command"]
            }
        }
    },

    # ── Browser & Web ──
    {
        "type": "function",
        "function": {
            "name": "search_youtube",
            "description": "Search YouTube and automatically play the top video result in browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query or song title."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_google",
            "description": "Search Google and return top search result snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Google search query."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_quick_search",
            "description": "Fast instant web search for answering factual questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_url",
            "description": "Navigate browser directly to a website URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to open."}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_page_content",
            "description": "Extract text content from current active browser page.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]


def get_tool_map() -> Dict[str, Callable]:
    """Dynamically bind tool function map to current platform controllers."""
    plat = get_platform()
    return {
        # App controller
        "open_app": plat.apps.open_app,
        "close_app": plat.apps.close_app,
        "switch_to_app": plat.apps.switch_to_app,
        "get_running_apps": plat.apps.get_running_apps,
        "get_frontmost_app": plat.apps.get_frontmost_app,

        # System controller
        "set_volume": plat.system.set_volume,
        "get_volume": plat.system.get_volume,
        "mute_audio": plat.system.mute_audio,
        "unmute_audio": plat.system.unmute_audio,
        "set_brightness": plat.system.set_brightness,
        "get_system_info": plat.system.get_system_info,
        "get_running_processes": plat.system.get_running_processes,
        "open_settings": plat.system.open_settings,
        "lock_screen": plat.system.lock_screen,
        "sleep_system": plat.system.sleep_system,
        "shutdown_system": plat.system.shutdown_system,
        "restart_system": plat.system.restart_system,
        "empty_trash": plat.system.empty_trash,
        "show_desktop": plat.system.show_desktop,
        "show_notification": plat.system.show_notification,
        "create_note": plat.system.create_note,
        "create_reminder": plat.system.create_reminder,
        "open_file_manager": plat.system.open_file_manager,

        # Input controller
        "type_text": plat.input.type_text,
        "press_key": plat.input.press_key,
        "click_at": plat.input.click_at,
        "take_screenshot": plat.input.take_screenshot,
        "copy_to_clipboard": plat.input.copy_to_clipboard,
        "get_clipboard": plat.input.get_clipboard,
        "sleep_delay": sleep_delay,

        # Filesystem & Shell
        "get_standard_directory": get_standard_directory,
        "write_file": write_file,
        "read_file": read_file,
        "list_files": list_files,
        "delete_file": delete_file,
        "run_shell_command": run_shell_command,

        # Browser
        "search_youtube": search_youtube,
        "search_google": search_google,
        "web_quick_search": web_quick_search,
        "open_url": open_url,
        "get_page_content": get_page_content,
    }


def execute_tool(name: str, arguments: Dict[str, Any]) -> str:
    """Execute tool with timing, error handling, and metric telemetry."""
    tool_map = get_tool_map()
    if name not in tool_map:
        return f"Unknown tool: '{name}'"

    fn = tool_map[name]
    start_time = time.time()
    success = True
    err_str = None

    try:
        import inspect
        sig = inspect.signature(fn)
        params = sig.parameters
        has_var_kw = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())

        if has_var_kw:
            call_kwargs = arguments
        else:
            call_kwargs = {k: v for k, v in arguments.items() if k in params}

        res = fn(**call_kwargs)
        # BUG-16 fix: serialize dict/list results as proper JSON instead of Python repr
        # (Python str(dict) produces single-quoted strings that confuse the LLM)
        if isinstance(res, (dict, list)):
            import json as _json
            return _json.dumps(res, default=str, ensure_ascii=False)
        return str(res)
    except Exception as e:
        success = False
        err_str = str(e)
        return f"Error executing {name}: {str(e)}"
    finally:
        duration_ms = (time.time() - start_time) * 1000
        get_tracker().record_tool_call(
            tool_name=name,
            duration_ms=duration_ms,
            success=success,
            error=err_str
        )

"""
filesystem.py — Cross-Platform Pathlib-Based File Management Tools
Safe file creation, reading, listing, and deletion using Python standard pathlib.
"""

from pathlib import Path
from typing import Optional, Dict
from platform_layer import get_platform


def resolve_safe_path(path_str: str) -> Path:
    """Resolve and expand user paths (~ and relative paths) safely."""
    p = Path(path_str).expanduser()
    return p.resolve()


def get_standard_directory(name: str) -> str:
    """
    Get the absolute path of a standard user directory:
    'home', 'desktop', 'documents', 'downloads', 'pictures', 'videos', 'music'.
    """
    plat = get_platform()
    dirs = plat.get_standard_directories()
    key = name.strip().lower()
    if key in dirs:
        return dirs[key]
    return f"Unknown directory identifier '{name}'. Available: {', '.join(dirs.keys())}"


def write_file(path: str, content: str) -> str:
    """
    Create or overwrite a file with given text content.
    Automatically creates parent directories.
    """
    try:
        file_path = resolve_safe_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} characters to {file_path}"
    except Exception as e:
        return f"Error writing file '{path}': {str(e)}"


def read_file(path: str) -> str:
    """
    Read content of a text file from disk.
    """
    try:
        file_path = resolve_safe_path(path)
        if not file_path.exists():
            return f"Error: File '{path}' does not exist at {file_path}."
        if not file_path.is_file():
            return f"Error: '{path}' is a directory, not a file."

        content = file_path.read_text(encoding="utf-8", errors="replace")
        if len(content) > 50000:
            return content[:50000] + f"\n... [Truncated {len(content) - 50000} remaining characters]"
        return content
    except Exception as e:
        return f"Error reading file '{path}': {str(e)}"


def list_files(path: str = ".") -> str:
    """
    List contents of a directory.
    """
    try:
        dir_path = resolve_safe_path(path)
        if not dir_path.exists():
            return f"Error: Directory '{path}' does not exist."
        if not dir_path.is_dir():
            return f"Error: '{path}' is a file, not a directory."

        entries = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        lines = []
        for e in entries[:60]:
            kind = "[DIR] " if e.is_dir() else "[FILE]"
            size = f"({e.stat().st_size} bytes)" if e.is_file() else ""
            lines.append(f"  {kind} {e.name} {size}")

        summary = f"Contents of {dir_path} ({len(entries)} items):\n" + "\n".join(lines)
        if len(entries) > 60:
            summary += f"\n  ... and {len(entries) - 60} more items"
        return summary
    except Exception as e:
        return f"Error listing directory '{path}': {str(e)}"


def delete_file(path: str, confirm: bool = False) -> str:
    """
    Delete a file from disk. Requires explicit confirmation.
    """
    try:
        file_path = resolve_safe_path(path)
        if not file_path.exists():
            return f"File '{path}' does not exist."
        if not confirm:
            return f"WARNING: Deleting '{file_path}' is permanent. Pass confirm=True to proceed."

        if file_path.is_file():
            file_path.unlink()
            return f"Deleted file: {file_path}"
        elif file_path.is_dir():
            import shutil
            shutil.rmtree(file_path)
            return f"Deleted directory and its contents: {file_path}"
        return f"Could not delete {file_path}"
    except Exception as e:
        return f"Error deleting '{path}': {str(e)}"

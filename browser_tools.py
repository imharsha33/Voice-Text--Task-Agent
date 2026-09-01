"""
browser_tools.py — Backward-compatibility forwarding module for tools.browser
"""

from tools.browser import (
    open_url,
    search_youtube,
    search_google,
    get_page_content,
    web_quick_search,
)
from tools.registry import TOOL_DEFINITIONS

# Expose legacy aliases
BROWSER_TOOLS = [
    t for t in TOOL_DEFINITIONS
    if isinstance(t, dict)
    and isinstance(t.get("function"), dict)
    and t["function"].get("name") in [
        "open_url", "search_youtube", "search_google", "get_page_content", "web_quick_search"
    ]
]
BROWSER_TOOL_FUNCTIONS = {
    "open_url": open_url,
    "search_youtube": search_youtube,
    "search_google": search_google,
    "get_page_content": get_page_content,
    "web_quick_search": web_quick_search,
}

__all__ = [
    "open_url",
    "search_youtube",
    "search_google",
    "get_page_content",
    "web_quick_search",
    "BROWSER_TOOLS",
    "BROWSER_TOOL_FUNCTIONS",
]

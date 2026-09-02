"""
browser.py — Cross-Platform Playwright Browser Automation Tools
Provides browser control, YouTube playback, Google search, and page extraction.
"""

import asyncio
import threading
import time
import urllib.parse
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page, Playwright

_playwright: Optional[Playwright] = None
_browser: Optional[Browser] = None
_page: Optional[Page] = None
# BUG-04 fix: use thread-local storage for event loops instead of a single global loop.
# asyncio.set_event_loop() from a worker thread corrupts FastAPI's event loop.
_thread_local = threading.local()


async def _ensure_browser() -> Page:
    """Initialize Playwright browser instance if not running."""
    global _playwright, _browser, _page
    if _browser is None or not _browser.is_connected():
        _playwright = await async_playwright().start()
        try:
            _browser = await _playwright.chromium.launch(
                channel="chrome",
                headless=False,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
            )
        except Exception:
            _browser = await _playwright.chromium.launch(
                headless=False,
                args=["--start-maximized"]
            )
        context = await _browser.new_context(
            viewport=None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        _page = await context.new_page()
    elif _page is None or _page.is_closed():
        context = await _browser.new_context(viewport=None)
        _page = await context.new_page()
    return _page


def _run_async(coro):
    """Run async coroutine in a thread-local managed event loop.
    BUG-04 fix: uses thread-local loop instead of set_event_loop() so we
    never overwrite FastAPI/uvicorn's global event loop from worker threads.
    """
    loop = getattr(_thread_local, "loop", None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        _thread_local.loop = loop
    return loop.run_until_complete(coro)


async def _open_url_async(url: str) -> str:
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    try:
        page = await _ensure_browser()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(1)
        title = await page.title()
        return f"Opened {url} ('{title}')"
    except Exception as e:
        import webbrowser
        webbrowser.open(url)
        return f"Opened {url} in default browser"


async def _search_youtube_async(query: str) -> str:
    """Search YouTube and play the top matching video."""
    encoded = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded}"
    try:
        page = await _ensure_browser()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(1.5)

        # Dismiss cookie / promo popups
        try:
            dialog_btns = await page.query_selector_all(
                "button[aria-label*='Accept'], button[aria-label*='Agree'], tp-yt-paper-button#button"
            )
            for btn in dialog_btns[:2]:
                if await btn.is_visible():
                    await btn.click()
                    await asyncio.sleep(0.5)
        except Exception:
            pass

        # Click first video result
        selectors = [
            "ytd-video-renderer a#thumbnail",
            "ytd-video-renderer #video-title",
            "a#video-title",
            "#contents ytd-video-renderer a#thumbnail",
            "a.ytd-thumbnail"
        ]
        for selector in selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=4000)
                if element and await element.is_visible():
                    await element.click()
                    await asyncio.sleep(2)
                    title = await page.title()
                    return f"Playing '{title}' on YouTube"
            except Exception:
                continue

        return f"Searched YouTube for '{query}'"
    except Exception as e:
        import webbrowser
        webbrowser.open(url)
        return f"Opened YouTube search for '{query}' in default browser"


async def _search_google_async(query: str) -> str:
    """Search Google and return top search result snippets."""
    page = await _ensure_browser()
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(1.5)

    results = []
    try:
        elements = await page.query_selector_all("div.g, div[data-hveid]")
        for el in elements[:5]:
            title_el = await el.query_selector("h3")
            snippet_el = await el.query_selector("div.VwiC3b, span.aCOpRe")
            if title_el:
                title = (await title_el.inner_text()).strip()
                snippet = (await snippet_el.inner_text()).strip() if snippet_el else ""
                if title:
                    results.append(f"• {title}\n  {snippet}")
    except Exception:
        pass

    if results:
        return f"Google results for '{query}':\n\n" + "\n\n".join(results)
    return f"Searched Google for '{query}'"


async def _get_page_content_async() -> str:
    """Extract visible text content of current browser page."""
    page = await _ensure_browser()
    try:
        title = await page.title()
        url = page.url
        text = await page.evaluate("""() => {
            const el = document.querySelector('article, main, #content, .content') || document.body;
            return el ? el.innerText : '';
        }""")
        cleaned = " ".join(text.split())[:3000]
        return f"Page Title: {title}\nURL: {url}\n\nContent:\n{cleaned}"
    except Exception as e:
        return f"Error extracting page content: {str(e)}"


# Synchronous entry points for the tool dispatcher
def open_url(url: str) -> str:
    return _run_async(_open_url_async(url))


def search_youtube(query: str) -> str:
    return _run_async(_search_youtube_async(query))


def search_google(query: str) -> str:
    return _run_async(_search_google_async(query))


def get_page_content() -> str:
    return _run_async(_get_page_content_async())


def web_quick_search(query: str) -> str:
    """Quick search using httpx DuckDuckGo instant answer.
    BUG-11 fix: fallback is now a lightweight Google HTTP scrape instead of
    launching the full Playwright browser window.
    """
    import httpx
    import re
    try:
        encoded = urllib.parse.quote(query)
        resp = httpx.get(
            f"https://html.duckduckgo.com/html/?q={encoded}",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=8.0
        )
        if resp.status_code == 200:
            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', resp.text, re.DOTALL)
            clean_snippets = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:3] if s.strip()]
            if clean_snippets:
                return "\n".join(f"\u2022 {s}" for s in clean_snippets)
    except Exception:
        pass

    # Lightweight HTTP fallback: scrape Google results without launching a browser
    try:
        encoded = urllib.parse.quote(query)
        resp = httpx.get(
            f"https://www.google.com/search?q={encoded}",
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
            timeout=8.0,
            follow_redirects=True
        )
        if resp.status_code == 200:
            import re
            # Extract visible text snippets from Google HTML
            snippets = re.findall(r'<div class="[^"]*VwiC3b[^"]*"[^>]*>(.*?)</div>', resp.text, re.DOTALL)
            clean = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:3] if s.strip()]
            if clean:
                return "\n".join(f"\u2022 {s}" for s in clean)
    except Exception:
        pass

    return f"Could not find results for '{query}'. Try a more specific search."

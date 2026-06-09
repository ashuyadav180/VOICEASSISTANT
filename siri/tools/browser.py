"""Browser automation via Playwright."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

_browser = None
_page = None
_playwright = None


async def _ensure_browser():
    global _browser, _page, _playwright
    if _page is not None:
        return _page

    from playwright.async_api import async_playwright

    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(headless=False)
    context = await _browser.new_context()
    _page = await context.new_page()
    return _page


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _ok(result: Any) -> dict:
    return {"success": True, "result": result, "error": None}


def _err(msg: str) -> dict:
    return {"success": False, "result": None, "error": msg}


async def _browser_open(url: str) -> dict:
    page = await _ensure_browser()
    if not url.startswith("http"):
        url = f"https://{url}"
    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
    return _ok(page.url)


async def _browser_search(query: str) -> dict:
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    return await _browser_open(url)


async def _browser_get_text() -> dict:
    page = await _ensure_browser()
    text = await page.inner_text("body")
    return _ok(text[:8000])


async def _browser_click_element(selector_or_description: str) -> dict:
    page = await _ensure_browser()
    try:
        await page.click(selector_or_description, timeout=5000)
    except Exception:
        await page.get_by_text(selector_or_description, exact=False).first.click(timeout=5000)
    return _ok(f"Clicked {selector_or_description}")


async def _browser_fill_form(field: str, value: str) -> dict:
    page = await _ensure_browser()
    try:
        await page.fill(field, value, timeout=5000)
    except Exception:
        await page.get_by_label(field).fill(value, timeout=5000)
    return _ok(f"Filled {field}")


async def _browser_scroll(direction: str, amount: int = 500) -> dict:
    page = await _ensure_browser()
    delta = amount if direction.lower() in ("down", "bottom") else -amount
    await page.mouse.wheel(0, delta)
    return _ok(f"Scrolled {direction}")


async def _browser_screenshot() -> dict:
    page = await _ensure_browser()
    import base64

    data = await page.screenshot()
    return _ok({"base64": base64.b64encode(data).decode()})


async def _browser_new_tab(url: str = "") -> dict:
    global _page
    page = await _ensure_browser()
    _page = await page.context.new_page()
    if url:
        if not url.startswith("http"):
            url = f"https://{url}"
        await _page.goto(url)
    return _ok(_page.url)


async def _browser_close_tab() -> dict:
    global _page
    if _page:
        await _page.close()
        pages = _page.context.pages
        _page = pages[-1] if pages else None
    return _ok("Tab closed")


async def _youtube_search(query: str) -> dict:
    url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    return await _browser_open(url)


async def _youtube_play(title: str) -> dict:
    await _youtube_search(title)
    page = await _ensure_browser()
    await page.locator("ytd-video-renderer a#video-title").first.click(timeout=10000)
    return _ok(f"Playing {title}")


async def _youtube_pause() -> dict:
    page = await _ensure_browser()
    await page.keyboard.press("k")
    return _ok("Paused")


async def _youtube_next() -> dict:
    page = await _ensure_browser()
    await page.keyboard.press("Shift+n")
    return _ok("Next video")


def browser_open(url: str) -> dict:
    return _run(_browser_open(url))


def browser_search(query: str) -> dict:
    return _run(_browser_search(query))


def browser_get_text() -> dict:
    return _run(_browser_get_text())


def browser_click_element(selector_or_description: str) -> dict:
    return _run(_browser_click_element(selector_or_description))


def browser_fill_form(field: str, value: str) -> dict:
    return _run(_browser_fill_form(field, value))


def browser_scroll(direction: str, amount: int = 500) -> dict:
    return _run(_browser_scroll(direction, amount))


def browser_screenshot() -> dict:
    return _run(_browser_screenshot())


def browser_new_tab(url: str = "") -> dict:
    return _run(_browser_new_tab(url))


def browser_close_tab() -> dict:
    return _run(_browser_close_tab())


def youtube_search(query: str) -> dict:
    return _run(_youtube_search(query))


def youtube_play(title: str) -> dict:
    return _run(_youtube_play(title))


def youtube_pause() -> dict:
    return _run(_youtube_pause())


def youtube_next() -> dict:
    return _run(_youtube_next())

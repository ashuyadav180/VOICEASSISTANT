"""Computer control tools: mouse, keyboard, screenshot, windows."""

from __future__ import annotations

import base64
import io
import logging
from typing import Any

import mss
import pyautogui

logger = logging.getLogger(__name__)
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05

try:
    import pygetwindow as gw

    GW_AVAILABLE = True
except ImportError:
    GW_AVAILABLE = False


def _ok(result: Any) -> dict:
    return {"success": True, "result": result, "error": None}


def _err(msg: str) -> dict:
    return {"success": False, "result": None, "error": msg}


def mouse_click(x: int, y: int, button: str = "left", clicks: int = 1) -> dict:
    try:
        pyautogui.click(x=x, y=y, button=button, clicks=clicks)
        return _ok(f"Clicked ({x}, {y})")
    except Exception as e:
        return _err(str(e))


def mouse_move(x: int, y: int, duration: float = 0.3) -> dict:
    try:
        pyautogui.moveTo(x, y, duration=duration)
        return _ok(f"Moved to ({x}, {y})")
    except Exception as e:
        return _err(str(e))


def mouse_scroll(x: int = 0, y: int = 0, amount: int = 3) -> dict:
    try:
        pyautogui.scroll(amount, x=x, y=y)
        return _ok(f"Scrolled {amount}")
    except Exception as e:
        return _err(str(e))


def keyboard_type(text: str) -> dict:
    try:
        pyautogui.write(text, interval=0.02) if text.isascii() else pyautogui.typewrite(text)
        return _ok(f"Typed {len(text)} chars")
    except Exception:
        try:
            import pyperclip

            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")
            return _ok(f"Pasted {len(text)} chars")
        except Exception as e:
            return _err(str(e))


def keyboard_hotkey(keys: list[str]) -> dict:
    try:
        pyautogui.hotkey(*keys)
        return _ok(f"Pressed {'+'.join(keys)}")
    except Exception as e:
        return _err(str(e))


def keyboard_press(key: str) -> dict:
    try:
        pyautogui.press(key)
        return _ok(f"Pressed {key}")
    except Exception as e:
        return _err(str(e))


def drag_and_drop(x1: int, y1: int, x2: int, y2: int) -> dict:
    try:
        pyautogui.moveTo(x1, y1)
        pyautogui.drag(x2 - x1, y2 - y1, duration=0.5)
        return _ok(f"Dragged ({x1},{y1}) to ({x2},{y2})")
    except Exception as e:
        return _err(str(e))


def take_screenshot() -> dict:
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            img = sct.grab(monitor)
            from PIL import Image

            pil = Image.frombytes("RGB", img.size, img.bgra, "raw", "BGRX")
            buf = io.BytesIO()
            pil.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            return _ok({"base64": b64, "width": img.width, "height": img.height})
    except Exception as e:
        return _err(str(e))


def get_active_window() -> dict:
    if not GW_AVAILABLE:
        return _err("pygetwindow not available")
    try:
        win = gw.getActiveWindow()
        return _ok(win.title if win else "No active window")
    except Exception as e:
        return _err(str(e))


def _find_window(title: str):
    if not GW_AVAILABLE:
        return None
    matches = [w for w in gw.getAllWindows() if title.lower() in w.title.lower()]
    return matches[0] if matches else None


def focus_window(title: str) -> dict:
    win = _find_window(title)
    if not win:
        return _err(f"Window not found: {title}")
    try:
        win.activate()
        return _ok(f"Focused {win.title}")
    except Exception as e:
        return _err(str(e))


def minimize_window(title: str) -> dict:
    win = _find_window(title)
    if not win:
        return _err(f"Window not found: {title}")
    try:
        win.minimize()
        return _ok(f"Minimized {win.title}")
    except Exception as e:
        return _err(str(e))


def close_window(title: str) -> dict:
    win = _find_window(title)
    if not win:
        return _err(f"Window not found: {title}")
    try:
        win.close()
        return _ok(f"Closed {win.title}")
    except Exception as e:
        return _err(str(e))

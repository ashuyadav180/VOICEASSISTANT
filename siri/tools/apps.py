"""Application launcher tools for Windows."""

from __future__ import annotations

import os
import subprocess
from typing import Any

try:
    import psutil
    import pygetwindow as gw

    GW_AVAILABLE = True
except ImportError:
    GW_AVAILABLE = False

# Common Windows app mappings
APP_MAP = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "vscode": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "vs code": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "visual studio code": r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "spotify": r"C:\Users\{user}\AppData\Roaming\Spotify\Spotify.exe",
    "terminal": "wt.exe",
    "windows terminal": "wt.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "settings": "ms-settings:",
    "paint": "mspaint.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "outlook": "outlook.exe",
}


def _ok(result: Any) -> dict:
    return {"success": True, "result": result, "error": None}


def _err(msg: str) -> dict:
    return {"success": False, "result": None, "error": msg}


def _resolve_app_path(name: str) -> str:
    key = name.lower().strip()
    path = APP_MAP.get(key, name)
    user = os.environ.get("USERNAME", "")
    return path.replace("{user}", user)


def open_app(name: str) -> dict:
    try:
        path = _resolve_app_path(name)
        if path.endswith(":"):
            os.startfile(path)
        elif os.path.isfile(path):
            subprocess.Popen([path], shell=False)
        else:
            # Try as command / start menu search
            subprocess.Popen(f'start "" "{path}"', shell=True)
        return _ok(f"Opened {name}")
    except Exception as e:
        return _err(str(e))


def close_app(name: str) -> dict:
    if not GW_AVAILABLE:
        return _err("pygetwindow not available")
    try:
        closed = []
        for w in gw.getAllWindows():
            if name.lower() in w.title.lower():
                w.close()
                closed.append(w.title)
        if closed:
            return _ok(closed)
        return _err(f"No window matching '{name}'")
    except Exception as e:
        return _err(str(e))


def list_running_apps() -> dict:
    try:
        apps = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                apps.append({"pid": proc.info["pid"], "name": proc.info["name"]})
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        unique = {a["name"]: a for a in apps}
        return _ok(list(unique.values())[:100])
    except Exception as e:
        return _err(str(e))


def switch_to_app(name: str) -> dict:
    if not GW_AVAILABLE:
        return _err("pygetwindow not available")
    try:
        for w in gw.getAllWindows():
            if name.lower() in w.title.lower():
                w.activate()
                return _ok(w.title)
        return _err(f"App not found: {name}")
    except Exception as e:
        return _err(str(e))

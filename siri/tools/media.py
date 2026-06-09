"""Media control tools."""

from __future__ import annotations

import subprocess
from typing import Any

from siri.tools import apps, browser


def _ok(result: Any) -> dict:
    return {"success": True, "result": result, "error": None}


def _err(msg: str) -> dict:
    return {"success": False, "result": None, "error": msg}


def spotify_play(song_or_artist: str) -> dict:
    apps.open_app("spotify")
    import time

    time.sleep(2)
    import pyautogui

    pyautogui.hotkey("ctrl", "l")
    pyautogui.write(song_or_artist, interval=0.03)
    pyautogui.press("enter")
    time.sleep(1)
    pyautogui.press("enter")
    return _ok(f"Playing {song_or_artist}")


def spotify_pause() -> dict:
    import pyautogui

    pyautogui.press("playpause")
    return _ok("Spotify paused")


def spotify_next() -> dict:
    import pyautogui

    pyautogui.hotkey("ctrl", "right")
    return _ok("Next track")


def spotify_volume(level: int) -> dict:
    from siri.tools import system

    return system.set_volume(level)


def play_local_music(filename: str) -> dict:
    try:
        import os
        from pathlib import Path

        path = Path(filename).expanduser().resolve()
        os.startfile(str(path))
        return _ok(str(path))
    except Exception as e:
        return _err(str(e))


def take_photo(save_path: str) -> dict:
    try:
        import cv2
        from pathlib import Path

        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return _err("Could not capture from webcam")
        p = Path(save_path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(p), frame)
        return _ok(str(p))
    except Exception as e:
        return _err(str(e))

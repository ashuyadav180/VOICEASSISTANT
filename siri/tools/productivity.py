"""Productivity tools: notes, reminders, calendar."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from siri.tools import browser as browser_tools


def _ok(result: Any) -> dict:
    return {"success": True, "result": result, "error": None}


def _err(msg: str) -> dict:
    return {"success": False, "result": None, "error": msg}


def take_note(title: str, content: str, notes_dir: Path | None = None) -> dict:
    try:
        from siri.config import config

        ndir = notes_dir or config.notes_dir
        ndir.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")[:50]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = ndir / f"{ts}_{safe}.md"
        path.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")
        return _ok(str(path))
    except Exception as e:
        return _err(str(e))


def read_notes(query: str, notes_dir: Path | None = None) -> dict:
    try:
        from siri.config import config

        ndir = notes_dir or config.notes_dir
        matches = []
        for f in ndir.glob("*.md"):
            text = f.read_text(encoding="utf-8", errors="replace")
            if query.lower() in text.lower() or query.lower() in f.name.lower():
                matches.append({"file": str(f), "preview": text[:300]})
        return _ok(matches)
    except Exception as e:
        return _err(str(e))


def set_reminder(message: str, time: str) -> dict:
    try:
        from siri.config import config

        reminders_file = config.data_dir / "reminders.json"
        reminders = []
        if reminders_file.exists():
            reminders = json.loads(reminders_file.read_text())
        reminders.append({
            "message": message,
            "time": time,
            "created": datetime.now().isoformat(),
            "done": False,
        })
        reminders_file.write_text(json.dumps(reminders, indent=2))
        return _ok(f"Reminder set for {time}: {message}")
    except Exception as e:
        return _err(str(e))


def create_calendar_event(title: str, date: str, time: str, duration: int = 60) -> dict:
    result = browser_tools.browser_open("https://calendar.google.com/calendar/u/0/r/eventedit")
    if not result["success"]:
        return result
    browser_tools.browser_fill_form('input[aria-label="Add title"]', title)
    return _ok(f"Calendar event '{title}' opened for {date} at {time}")


def read_calendar_today() -> dict:
    result = browser_tools.browser_open("https://calendar.google.com/calendar/u/0/r/day")
    if not result["success"]:
        return result
    text = browser_tools.browser_get_text()
    return _ok(text.get("result", "")[:2000] if text["success"] else "Could not read calendar")

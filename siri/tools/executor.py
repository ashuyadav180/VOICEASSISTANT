"""Tool executor — dispatches tool calls to implementations."""

from __future__ import annotations

import logging
from typing import Any, Callable

from siri.config import Config
from siri.tools import (
    apps,
    browser,
    code,
    communication,
    computer,
    filesystem,
    media,
    productivity,
    search,
    system,
    research,
    research_graph,
    research_summarize,
)
from siri.memory import library
from siri.tools.registry import CONFIRMATION_REQUIRED

logger = logging.getLogger(__name__)


class ToolExecutor:
    def __init__(self, config: Config) -> None:
        self.config = config
        self._pending_confirmations: dict[str, dict] = {}
        self._handlers: dict[str, Callable] = self._build_handlers()

    def _build_handlers(self) -> dict[str, Callable]:
        return {
            # Computer
            "mouse_click": computer.mouse_click,
            "mouse_move": computer.mouse_move,
            "mouse_scroll": computer.mouse_scroll,
            "keyboard_type": computer.keyboard_type,
            "keyboard_hotkey": lambda keys: computer.keyboard_hotkey(keys),
            "keyboard_press": computer.keyboard_press,
            "drag_and_drop": computer.drag_and_drop,
            "take_screenshot": computer.take_screenshot,
            "get_active_window": computer.get_active_window,
            "focus_window": computer.focus_window,
            "minimize_window": computer.minimize_window,
            "close_window": computer.close_window,
            # Filesystem
            "read_file": filesystem.read_file,
            "write_file": filesystem.write_file,
            "append_file": filesystem.append_file,
            "delete_file": filesystem.delete_file,
            "move_file": filesystem.move_file,
            "copy_file": filesystem.copy_file,
            "list_directory": filesystem.list_directory,
            "create_folder": filesystem.create_folder,
            "search_files": filesystem.search_files,
            "open_file": filesystem.open_file,
            "zip_folder": filesystem.zip_folder,
            "unzip_file": filesystem.unzip_file,
            # Apps
            "open_app": apps.open_app,
            "close_app": apps.close_app,
            "list_running_apps": apps.list_running_apps,
            "switch_to_app": apps.switch_to_app,
            # Browser
            "browser_open": browser.browser_open,
            "browser_search": browser.browser_search,
            "browser_get_text": browser.browser_get_text,
            "browser_click_element": browser.browser_click_element,
            "browser_fill_form": browser.browser_fill_form,
            "browser_scroll": browser.browser_scroll,
            "browser_screenshot": browser.browser_screenshot,
            "browser_new_tab": browser.browser_new_tab,
            "browser_close_tab": browser.browser_close_tab,
            "youtube_search": browser.youtube_search,
            "youtube_play": browser.youtube_play,
            "youtube_pause": browser.youtube_pause,
            "youtube_next": browser.youtube_next,
            # System
            "get_battery_status": system.get_battery_status,
            "get_wifi_status": system.get_wifi_status,
            "set_volume": system.set_volume,
            "mute_audio": system.mute_audio,
            "unmute_audio": system.unmute_audio,
            "shutdown": system.shutdown,
            "restart": system.restart,
            "sleep_system": system.sleep_system,
            "get_cpu_usage": system.get_cpu_usage,
            "get_ram_usage": system.get_ram_usage,
            "get_disk_usage": system.get_disk_usage,
            "get_running_processes": system.get_running_processes,
            "kill_process": system.kill_process,
            "clipboard_get": system.clipboard_get,
            "clipboard_set": system.clipboard_set,
            "lock_screen": system.lock_screen,
            # Code
            "run_python": code.run_python,
            "run_terminal_command": code.run_terminal_command,
            "run_js": code.run_js,
            "open_terminal": code.open_terminal,
            "create_and_run_script": code.create_and_run_script,
            # Communication
            "send_whatsapp": communication.send_whatsapp,
            "compose_email": communication.compose_email,
            "send_email": communication.send_email,
            "read_latest_emails": communication.read_latest_emails,
            # Productivity
            "create_calendar_event": productivity.create_calendar_event,
            "read_calendar_today": productivity.read_calendar_today,
            "set_reminder": productivity.set_reminder,
            "take_note": productivity.take_note,
            "read_notes": productivity.read_notes,
            "search_web": lambda query: search.search_web(query, self.config.tavily_api_key),
            "summarize_webpage": search.summarize_webpage,
            "translate_text": search.translate_text,
            # Media
            "spotify_play": media.spotify_play,
            "spotify_pause": media.spotify_pause,
            "spotify_next": media.spotify_next,
            "spotify_volume": media.spotify_volume,
            "play_local_music": media.play_local_music,
            "take_photo": media.take_photo,
            # AI / search
            "search_arxiv": search.search_arxiv,
            "search_github": search.search_github,
            # Research
            "search_semantic": research.search_semantic,
            "search_pubmed": research.search_pubmed,
            "get_author_profile": research.get_author_profile,
            "analyze_trend": research.analyze_trend,
            "build_citation_graph": research_graph.build_citation_graph,
            "summarize_paper": research_summarize.summarize_paper,
            "library_save": library.library_save,
            "library_search": library.library_search,
        }

    def execute(self, name: str, arguments: dict[str, Any], confirmed: bool = False) -> dict:
        if name not in self._handlers:
            return {"success": False, "result": None, "error": f"Unknown tool: {name}"}

        if name in CONFIRMATION_REQUIRED and not confirmed:
            self._pending_confirmations[name] = arguments
            return {
                "success": False,
                "result": None,
                "error": f"CONFIRMATION_REQUIRED: {name} needs user approval. Ask user to say 'yes' to proceed.",
                "needs_confirmation": True,
            }

        try:
            handler = self._handlers[name]
            result = handler(**arguments)
            logger.info("Tool %s → success=%s", name, result.get("success"))
            return result
        except TypeError as e:
            return {"success": False, "result": None, "error": f"Invalid arguments for {name}: {e}"}
        except Exception as e:
            logger.exception("Tool %s failed", name)
            return {"success": False, "result": None, "error": str(e)}

    def confirm_pending(self, tool_name: str | None = None) -> dict | None:
        if tool_name and tool_name in self._pending_confirmations:
            args = self._pending_confirmations.pop(tool_name)
            return self.execute(tool_name, args, confirmed=True)
        if self._pending_confirmations:
            name = next(iter(self._pending_confirmations))
            args = self._pending_confirmations.pop(name)
            return self.execute(name, args, confirmed=True)
        return None

    def has_pending_confirmation(self) -> bool:
        return bool(self._pending_confirmations)

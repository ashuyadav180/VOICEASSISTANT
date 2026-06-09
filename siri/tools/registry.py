"""Tool registry with JSON schemas for LLM function calling."""

from __future__ import annotations

from typing import Any

TOOL_SCHEMAS: list[dict[str, Any]] = [
    # Computer
    {"name": "mouse_click", "description": "Click mouse at screen coordinates", "parameters": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "button": {"type": "string", "default": "left"}, "clicks": {"type": "integer", "default": 1}}, "required": ["x", "y"]}},
    {"name": "mouse_move", "description": "Move mouse to coordinates", "parameters": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "duration": {"type": "number", "default": 0.3}}, "required": ["x", "y"]}},
    {"name": "mouse_scroll", "description": "Scroll mouse wheel", "parameters": {"type": "object", "properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "amount": {"type": "integer"}}, "required": ["amount"]}},
    {"name": "keyboard_type", "description": "Type text via keyboard", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "keyboard_hotkey", "description": "Press keyboard shortcut", "parameters": {"type": "object", "properties": {"keys": {"type": "array", "items": {"type": "string"}}}, "required": ["keys"]}},
    {"name": "keyboard_press", "description": "Press a single key", "parameters": {"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}},
    {"name": "drag_and_drop", "description": "Drag from one point to another", "parameters": {"type": "object", "properties": {"x1": {"type": "integer"}, "y1": {"type": "integer"}, "x2": {"type": "integer"}, "y2": {"type": "integer"}}, "required": ["x1", "y1", "x2", "y2"]}},
    {"name": "take_screenshot", "description": "Capture screen screenshot", "parameters": {"type": "object", "properties": {}}},
    {"name": "get_active_window", "description": "Get title of active window", "parameters": {"type": "object", "properties": {}}},
    {"name": "focus_window", "description": "Focus a window by title", "parameters": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}},
    {"name": "minimize_window", "description": "Minimize a window", "parameters": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}},
    {"name": "close_window", "description": "Close a window by title", "parameters": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}},
    # Filesystem
    {"name": "read_file", "description": "Read file contents", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "write_file", "description": "Write content to file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "append_file", "description": "Append content to file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "delete_file", "description": "Delete a file (requires confirmation)", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "move_file", "description": "Move file", "parameters": {"type": "object", "properties": {"src": {"type": "string"}, "dst": {"type": "string"}}, "required": ["src", "dst"]}},
    {"name": "copy_file", "description": "Copy file", "parameters": {"type": "object", "properties": {"src": {"type": "string"}, "dst": {"type": "string"}}, "required": ["src", "dst"]}},
    {"name": "list_directory", "description": "List directory contents", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "create_folder", "description": "Create a folder", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "search_files", "description": "Search files by glob pattern", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "root_path": {"type": "string"}}, "required": ["query"]}},
    {"name": "open_file", "description": "Open file with default app", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "zip_folder", "description": "Zip a folder", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "output": {"type": "string"}}, "required": ["path", "output"]}},
    {"name": "unzip_file", "description": "Unzip an archive", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "destination": {"type": "string"}}, "required": ["path", "destination"]}},
    # Apps
    {"name": "open_app", "description": "Open an application", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
    {"name": "close_app", "description": "Close an application", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
    {"name": "list_running_apps", "description": "List running applications", "parameters": {"type": "object", "properties": {}}},
    {"name": "switch_to_app", "description": "Switch to an application", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
    # Browser
    {"name": "browser_open", "description": "Open URL in browser", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
    {"name": "browser_search", "description": "Google search in browser", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "browser_get_text", "description": "Get visible text from browser", "parameters": {"type": "object", "properties": {}}},
    {"name": "browser_click_element", "description": "Click element in browser", "parameters": {"type": "object", "properties": {"selector_or_description": {"type": "string"}}, "required": ["selector_or_description"]}},
    {"name": "browser_fill_form", "description": "Fill form field in browser", "parameters": {"type": "object", "properties": {"field": {"type": "string"}, "value": {"type": "string"}}, "required": ["field", "value"]}},
    {"name": "browser_scroll", "description": "Scroll browser page", "parameters": {"type": "object", "properties": {"direction": {"type": "string"}, "amount": {"type": "integer"}}, "required": ["direction"]}},
    {"name": "browser_screenshot", "description": "Screenshot current browser tab", "parameters": {"type": "object", "properties": {}}},
    {"name": "browser_new_tab", "description": "Open new browser tab", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}}},
    {"name": "browser_close_tab", "description": "Close current browser tab", "parameters": {"type": "object", "properties": {}}},
    {"name": "youtube_search", "description": "Search YouTube", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "youtube_play", "description": "Play YouTube video by title", "parameters": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]}},
    {"name": "youtube_pause", "description": "Pause YouTube playback", "parameters": {"type": "object", "properties": {}}},
    {"name": "youtube_next", "description": "Next YouTube video", "parameters": {"type": "object", "properties": {}}},
    # System
    {"name": "get_battery_status", "description": "Get battery percentage and charging state", "parameters": {"type": "object", "properties": {}}},
    {"name": "get_wifi_status", "description": "Get WiFi connection status", "parameters": {"type": "object", "properties": {}}},
    {"name": "set_volume", "description": "Set system volume 0-100", "parameters": {"type": "object", "properties": {"level_0_to_100": {"type": "integer"}}, "required": ["level_0_to_100"]}},
    {"name": "mute_audio", "description": "Mute system audio", "parameters": {"type": "object", "properties": {}}},
    {"name": "unmute_audio", "description": "Unmute system audio", "parameters": {"type": "object", "properties": {}}},
    {"name": "shutdown", "description": "Shutdown system (requires confirmation)", "parameters": {"type": "object", "properties": {"delay_seconds": {"type": "integer", "default": 0}}}},
    {"name": "restart", "description": "Restart system (requires confirmation)", "parameters": {"type": "object", "properties": {"delay_seconds": {"type": "integer", "default": 0}}}},
    {"name": "sleep_system", "description": "Put system to sleep (requires confirmation)", "parameters": {"type": "object", "properties": {}}},
    {"name": "get_cpu_usage", "description": "Get CPU usage percentage", "parameters": {"type": "object", "properties": {}}},
    {"name": "get_ram_usage", "description": "Get RAM usage", "parameters": {"type": "object", "properties": {}}},
    {"name": "get_disk_usage", "description": "Get disk usage", "parameters": {"type": "object", "properties": {}}},
    {"name": "get_running_processes", "description": "List running processes", "parameters": {"type": "object", "properties": {}}},
    {"name": "kill_process", "description": "Kill a process (requires confirmation)", "parameters": {"type": "object", "properties": {"name_or_pid": {"type": "string"}}, "required": ["name_or_pid"]}},
    {"name": "clipboard_get", "description": "Get clipboard text", "parameters": {"type": "object", "properties": {}}},
    {"name": "clipboard_set", "description": "Set clipboard text", "parameters": {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}},
    {"name": "lock_screen", "description": "Lock the screen (requires confirmation)", "parameters": {"type": "object", "properties": {}}},
    # Code
    {"name": "run_python", "description": "Execute Python code", "parameters": {"type": "object", "properties": {"code_string": {"type": "string"}}, "required": ["code_string"]}},
    {"name": "run_terminal_command", "description": "Run shell command", "parameters": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "run_js", "description": "Execute JavaScript via Node.js", "parameters": {"type": "object", "properties": {"code_string": {"type": "string"}}, "required": ["code_string"]}},
    {"name": "open_terminal", "description": "Open terminal window", "parameters": {"type": "object", "properties": {}}},
    {"name": "create_and_run_script", "description": "Create and run a script file", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}, "code": {"type": "string"}}, "required": ["filename", "code"]}},
    # Communication
    {"name": "send_whatsapp", "description": "Send WhatsApp message", "parameters": {"type": "object", "properties": {"contact": {"type": "string"}, "message": {"type": "string"}}, "required": ["contact", "message"]}},
    {"name": "compose_email", "description": "Compose email in Gmail", "parameters": {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["to", "subject", "body"]}},
    {"name": "send_email", "description": "Send composed email", "parameters": {"type": "object", "properties": {}}},
    {"name": "read_latest_emails", "description": "Read latest emails", "parameters": {"type": "object", "properties": {"count": {"type": "integer", "default": 5}}}},
    # Productivity
    {"name": "create_calendar_event", "description": "Create calendar event", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "date": {"type": "string"}, "time": {"type": "string"}, "duration": {"type": "integer"}}, "required": ["title", "date", "time"]}},
    {"name": "read_calendar_today", "description": "Read today's calendar events", "parameters": {"type": "object", "properties": {}}},
    {"name": "set_reminder", "description": "Set a reminder", "parameters": {"type": "object", "properties": {"message": {"type": "string"}, "time": {"type": "string"}}, "required": ["message", "time"]}},
    {"name": "take_note", "description": "Save a note as markdown", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}}, "required": ["title", "content"]}},
    {"name": "read_notes", "description": "Search notes", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "search_web", "description": "Search the web via Tavily", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "summarize_webpage", "description": "Summarize a webpage URL", "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}},
    {"name": "translate_text", "description": "Translate text", "parameters": {"type": "object", "properties": {"text": {"type": "string"}, "target_language": {"type": "string"}}, "required": ["text", "target_language"]}},
    # Media
    {"name": "spotify_play", "description": "Play song on Spotify", "parameters": {"type": "object", "properties": {"song_or_artist": {"type": "string"}}, "required": ["song_or_artist"]}},
    {"name": "spotify_pause", "description": "Pause Spotify", "parameters": {"type": "object", "properties": {}}},
    {"name": "spotify_next", "description": "Next Spotify track", "parameters": {"type": "object", "properties": {}}},
    {"name": "spotify_volume", "description": "Set Spotify volume", "parameters": {"type": "object", "properties": {"level": {"type": "integer"}}, "required": ["level"]}},
    {"name": "play_local_music", "description": "Play local music file", "parameters": {"type": "object", "properties": {"filename": {"type": "string"}}, "required": ["filename"]}},
    {"name": "take_photo", "description": "Capture webcam photo", "parameters": {"type": "object", "properties": {"save_path": {"type": "string"}}, "required": ["save_path"]}},
    # AI
    {"name": "generate_image", "description": "Generate image from prompt", "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}}, "required": ["prompt"]}},
    {"name": "summarize_document", "description": "Summarize a document file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "draft_email", "description": "Draft email content with AI", "parameters": {"type": "object", "properties": {"context": {"type": "string"}}, "required": ["context"]}},
    {"name": "explain_screen", "description": "Describe what's on screen", "parameters": {"type": "object", "properties": {}}},
    {"name": "answer_from_screen", "description": "Answer question about screen content", "parameters": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]}},
    {"name": "code_review", "description": "Review a code file", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}},
    {"name": "search_arxiv", "description": "Search arXiv papers", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    {"name": "search_github", "description": "Search GitHub repositories", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
    # Research
    {"name": "search_semantic", "description": "Search Semantic Scholar for papers semantically", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 5}}, "required": ["query"]}},
    {"name": "search_pubmed", "description": "Search PubMed for medical/biology papers", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 5}}, "required": ["query"]}},
    {"name": "get_author_profile", "description": "Get author citations and h-index", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}},
    {"name": "analyze_trend", "description": "Analyze paper publication trends over last 5 years", "parameters": {"type": "object", "properties": {"topic": {"type": "string"}}, "required": ["topic"]}},
    {"name": "build_citation_graph", "description": "Build citation network for a paper to find key references and papers that cite it", "parameters": {"type": "object", "properties": {"seed_doi_or_title": {"type": "string"}}, "required": ["seed_doi_or_title"]}},
    {"name": "summarize_paper", "description": "Fetch TLDR and abstract for a research paper", "parameters": {"type": "object", "properties": {"doi_or_title": {"type": "string"}}, "required": ["doi_or_title"]}},
    {"name": "library_save", "description": "Save a paper to your local ChromaDB library", "parameters": {"type": "object", "properties": {"title": {"type": "string"}, "abstract": {"type": "string"}, "metadata": {"type": "object"}}, "required": ["title", "abstract"]}},
    {"name": "library_search", "description": "Semantic search across papers you have saved locally", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "n_results": {"type": "integer", "default": 3}}, "required": ["query"]}},
]

CONFIRMATION_REQUIRED = {
    "delete_file",
    "shutdown",
    "restart",
    "sleep_system",
    "kill_process",
    "lock_screen",
    "send_email",
    "send_whatsapp",
}


def get_openai_tools() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": s["name"],
                "description": s["description"],
                "parameters": s["parameters"],
            },
        }
        for s in TOOL_SCHEMAS
    ]


def get_anthropic_tools() -> list[dict]:
    return [
        {
            "name": s["name"],
            "description": s["description"],
            "input_schema": s["parameters"],
        }
        for s in TOOL_SCHEMAS
    ]

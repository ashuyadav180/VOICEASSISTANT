"""Short-term conversation memory (rolling window)."""

from __future__ import annotations

from collections import deque
from typing import Any


class ShortTermMemory:
    def __init__(self, max_turns: int = 15) -> None:
        self.max_turns = max_turns
        self._messages: deque[dict[str, str]] = deque(maxlen=max_turns * 2)

    def add(self, role: str, content: str) -> None:
        self._messages.append({"role": role, "content": content})

    def get_messages(self) -> list[dict[str, str]]:
        return list(self._messages)

    def clear(self) -> None:
        self._messages.clear()

    def to_context(self) -> list[dict[str, Any]]:
        return [{"role": m["role"], "content": m["content"]} for m in self._messages]

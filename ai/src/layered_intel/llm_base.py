from __future__ import annotations

from typing import Any, Protocol


class ChatClient(Protocol):
    def chat(self, messages: list[dict[str, Any]], *, temperature: float = 0.2) -> str: ...

    def chat_json(self, messages: list[dict[str, Any]], *, temperature: float = 0.1) -> dict[str, Any]: ...

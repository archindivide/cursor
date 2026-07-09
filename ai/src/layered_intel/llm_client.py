from __future__ import annotations

import json
from typing import Any

import httpx

from layered_intel.config import Settings


class OllamaClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.Client(timeout=120.0)

    def close(self) -> None:
        self._client.close()

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
        format_json: bool = False,
    ) -> str:
        url = f"{self._settings.ollama_base_url}/api/chat"
        payload: dict[str, Any] = {
            "model": self._settings.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if format_json:
            payload["format"] = "json"
        resp = self._client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        msg = data.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, str):
            raise RuntimeError(f"Unexpected Ollama response: {data!r}")
        return content

    def chat_json(self, messages: list[dict[str, Any]], *, temperature: float = 0.1) -> dict[str, Any]:
        raw = self.chat(messages, temperature=temperature, format_json=True)
        return json.loads(raw)

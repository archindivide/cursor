from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from layered_intel.agent.loop import AgentSession
from layered_intel.config import Settings
from layered_intel.memory.db import Database
from layered_intel.memory.profiles import ProfileStore


class _StubClient:
    def __init__(self, chats: deque[str], jsons: deque[dict]) -> None:
        self._chats = chats
        self._jsons = jsons

    def chat(self, messages: list[dict], *, temperature: float = 0.2) -> str:
        return self._chats.popleft()

    def chat_json(self, messages: list[dict], *, temperature: float = 0.1) -> dict:
        if self._jsons:
            return self._jsons.popleft()
        return {"patch": {}}

    def close(self) -> None:
        pass


def test_tool_round_trip(tmp_path: Path) -> None:
    sand = tmp_path / "sand"
    sand.mkdir()
    (sand / "note.txt").write_text("hello", encoding="utf-8")
    chats: deque[str] = deque(
        [
            'TOOL_CALL {"name": "read_sandbox_file", "arguments": {"path": "note.txt"}}',
            "I read note.txt; it says hello.",
        ]
    )
    jsons: deque[dict] = deque()
    settings = Settings(
        ollama_base_url="http://127.0.0.1:11434",
        model="stub",
        data_dir=tmp_path / "d",
        sandbox_dir=sand,
    )
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    s = AgentSession(settings, session_id="t1", client=_StubClient(chats, jsons))
    try:
        out = s.step("Read note.txt from sandbox")
        assert "hello" in out.assistant_text.lower()
    finally:
        s.close()


def test_continuity_in_prompt(tmp_path: Path) -> None:
    class _MemCheck:
        def __init__(self) -> None:
            self.step = 0

        def chat(self, messages: list[dict], *, temperature: float = 0.2) -> str:
            sys = messages[0]["content"]
            user = messages[-1]["content"]
            self.step += 1
            if self.step == 1:
                assert "codename" in user
                return "Acknowledged."
            assert "alpha-7" in sys, "episodic memory should appear in system context"
            assert "codename" in user.lower()
            return "Your codename is alpha-7."

        def chat_json(self, messages: list[dict], *, temperature: float = 0.1) -> dict:
            return {"patch": {}}

        def close(self) -> None:
            pass

    settings = Settings(
        ollama_base_url="http://127.0.0.1:11434",
        model="stub",
        data_dir=tmp_path / "d2",
        sandbox_dir=tmp_path / "sand2",
    )
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.sandbox_dir.mkdir(parents=True, exist_ok=True)
    c = _MemCheck()
    s = AgentSession(settings, session_id="mem", client=c)
    try:
        s.step("My codename is alpha-7 for this exercise.")
        s.step("What is my codename?")
        assert c.step == 2
    finally:
        s.close()


def test_user_model_patch_applied(tmp_path: Path) -> None:
    chats: deque[str] = deque(["Hello!"])
    jsons: deque[dict] = deque(
        [
            {"patch": {}},
            {"patch": {"preferred_name": "Sam", "facts": ["likes tests"]}},
        ]
    )
    settings = Settings(
        ollama_base_url="http://127.0.0.1:11434",
        model="stub",
        data_dir=tmp_path / "d3",
        sandbox_dir=tmp_path / "sand3",
    )
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.sandbox_dir.mkdir(parents=True, exist_ok=True)
    s = AgentSession(settings, client=_StubClient(chats, jsons))
    try:
        s.step("Hello!")
    finally:
        s.close()
    db = Database(settings.data_dir / "memory.sqlite3")
    try:
        uv, um = ProfileStore(db).load_user()
        assert um.preferred_name == "Sam"
        assert "likes tests" in um.facts
        assert uv >= 2
    finally:
        db.close()

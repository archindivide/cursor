from __future__ import annotations

import json
from pathlib import Path

from layered_intel.config import Settings
from layered_intel.memory.db import Database
from layered_intel.memory.episodic import EpisodicMemory
from layered_intel.memory.summaries import SummaryService


class _JsonStub:
    def chat_json(self, messages: list[dict], *, temperature: float = 0.1) -> dict:
        # Extract event ids from user payload
        payload = json.loads(messages[-1]["content"])
        ids = payload["event_ids"]
        return {"summary": "compressed", "cited_event_ids": ids}


def test_rolling_summary_marks_compressed(tmp_path: Path) -> None:
    db = Database(tmp_path / "m.sqlite3")
    mem = EpisodicMemory(db)
    svc = SummaryService(db, mem, batch_size=5)
    sid = "s1"
    ids: list[int] = []
    for i in range(12):
        ids.append(
            mem.append(
                session_id=sid,
                role="user",
                kind="message",
                content=f"msg {i}",
            )
        )
    settings = Settings(
        ollama_base_url="http://127.0.0.1:11434",
        model="stub",
        data_dir=tmp_path,
        sandbox_dir=tmp_path / "sand",
        summarize_event_threshold=10,
        recent_events_limit=20,
    )
    svc.maybe_roll_summary(
        session_id=sid,
        total_uncompressed_threshold=settings.summarize_event_threshold,
        llm=_JsonStub(),
    )
    assert db.query("SELECT COUNT(*) c FROM summaries", ())[0]["c"] == 1
    compressed = {int(r["id"]): int(r["compressed"]) for r in db.query("SELECT id, compressed FROM events", ())}
    for eid in ids[:5]:
        assert compressed[eid] == 1
    assert mem.count_uncompressed(sid) == 7

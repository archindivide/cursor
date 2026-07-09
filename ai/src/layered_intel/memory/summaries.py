from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Protocol

from layered_intel.memory.db import Database
from layered_intel.memory.episodic import EpisodicMemory, Event


def _format_events_for_summary(events: list[Event]) -> str:
    lines: list[str] = []
    for e in events:
        lines.append(f"id={e.id} role={e.role} kind={e.kind}: {e.content}")
    return "\n".join(lines)


class LLMBackend(Protocol):
    def chat_json(self, messages: list[dict], *, temperature: float = 0.1) -> dict: ...


class SummaryService:
    """Compresses oldest uncompressed events into a summary row with explicit event-id citations."""

    def __init__(self, db: Database, episodic: EpisodicMemory, *, batch_size: int = 20) -> None:
        self._db = db
        self._episodic = episodic
        self._batch_size = batch_size

    def maybe_roll_summary(
        self,
        *,
        session_id: str,
        total_uncompressed_threshold: int,
        llm: LLMBackend | None,
    ) -> None:
        if llm is None:
            return
        n = self._episodic.count_uncompressed(session_id)
        if n <= total_uncompressed_threshold:
            return
        batch = self._episodic.fetch_oldest_uncompressed_batch(session_id, self._batch_size)
        if len(batch) < self._batch_size:
            return
        cited_ids = [e.id for e in batch]
        transcript = _format_events_for_summary(batch)
        messages = [
            {
                "role": "system",
                "content": (
                    "You compress conversation logs into a concise factual summary. "
                    "Return JSON with keys: summary (string), cited_event_ids (array of integers). "
                    "cited_event_ids MUST exactly match the provided event ids list, in any order."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"event_ids": cited_ids, "events_text": transcript},
                    ensure_ascii=False,
                ),
            },
        ]
        data = llm.chat_json(messages, temperature=0.1)
        body = str(data.get("summary", "")).strip()
        ids = data.get("cited_event_ids")
        if not body or not isinstance(ids, list):
            return
        parsed = [int(x) for x in ids if str(x).isdigit() or isinstance(x, int)]
        if set(parsed) != set(cited_ids):
            # Require full citation match to avoid silent drift
            return
        ts = datetime.now(timezone.utc).isoformat()
        self._db.execute(
            "INSERT INTO summaries (ts, session_id, body, cited_event_ids) VALUES (?, ?, ?, ?)",
            (ts, session_id, body, json.dumps(cited_ids)),
        )
        self._episodic.mark_compressed(cited_ids)

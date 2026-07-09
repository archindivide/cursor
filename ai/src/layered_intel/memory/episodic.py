from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from layered_intel.memory.db import Database


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Event:
    id: int
    ts: str
    session_id: str
    role: str
    kind: str
    content: str
    tool_name: str | None
    tool_args: dict[str, Any] | None
    tool_result: Any
    salience: str | None
    compressed: bool


class EpisodicMemory:
    def __init__(self, db: Database) -> None:
        self._db = db

    def append(
        self,
        *,
        session_id: str,
        role: str,
        kind: str,
        content: str,
        tool_name: str | None = None,
        tool_args: dict[str, Any] | None = None,
        tool_result: Any = None,
        salience: str | None = None,
    ) -> int:
        tool_args_s = json.dumps(tool_args) if tool_args is not None else None
        tool_result_s = json.dumps(tool_result) if tool_result is not None else None
        cur = self._db.execute(
            """
            INSERT INTO events (ts, session_id, role, kind, content, tool_name, tool_args, tool_result, salience)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _utc_now(),
                session_id,
                role,
                kind,
                content,
                tool_name,
                tool_args_s,
                tool_result_s,
                salience,
            ),
        )
        return int(cur.lastrowid)

    def mark_compressed(self, event_ids: list[int]) -> None:
        if not event_ids:
            return
        qmarks = ",".join("?" for _ in event_ids)
        self._db.execute(f"UPDATE events SET compressed = 1 WHERE id IN ({qmarks})", tuple(event_ids))

    def count_uncompressed(self, session_id: str) -> int:
        row = self._db.query_one(
            "SELECT COUNT(*) AS c FROM events WHERE session_id = ? AND compressed = 0",
            (session_id,),
        )
        return int(row["c"]) if row else 0

    def fetch_oldest_uncompressed_batch(self, session_id: str, limit: int) -> list[Event]:
        rows = self._db.query(
            """
            SELECT id, ts, session_id, role, kind, content, tool_name, tool_args, tool_result, salience, compressed
            FROM events
            WHERE session_id = ? AND compressed = 0
            ORDER BY id ASC
            LIMIT ?
            """,
            (session_id, limit),
        )
        return [_row_to_event(r) for r in rows]

    def fetch_recent_uncompressed(self, session_id: str, limit: int) -> list[Event]:
        rows = self._db.query(
            """
            SELECT id, ts, session_id, role, kind, content, tool_name, tool_args, tool_result, salience, compressed
            FROM events
            WHERE session_id = ? AND compressed = 0
            ORDER BY id DESC
            LIMIT ?
            """,
            (session_id, limit),
        )
        rows = list(reversed(rows))
        return [_row_to_event(r) for r in rows]

    def fetch_summaries(self, session_id: str) -> list[tuple[int, str, list[int]]]:
        rows = self._db.query(
            "SELECT id, body, cited_event_ids FROM summaries WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        )
        out: list[tuple[int, str, list[int]]] = []
        for r in rows:
            cited = json.loads(r["cited_event_ids"])
            if not isinstance(cited, list):
                cited = []
            out.append((int(r["id"]), str(r["body"]), [int(x) for x in cited]))
        return out


def _row_to_event(r: Any) -> Event:
    args = json.loads(r["tool_args"]) if r["tool_args"] else None
    tres = json.loads(r["tool_result"]) if r["tool_result"] else None
    return Event(
        id=int(r["id"]),
        ts=str(r["ts"]),
        session_id=str(r["session_id"]),
        role=str(r["role"]),
        kind=str(r["kind"]),
        content=str(r["content"]),
        tool_name=r["tool_name"],
        tool_args=args if isinstance(args, dict) else None,
        tool_result=tres,
        salience=r["salience"],
        compressed=bool(r["compressed"]),
    )

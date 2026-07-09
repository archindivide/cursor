from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Protocol

from layered_intel.memory.db import Database
from layered_intel.models.self_user import SelfModel, UserModel, merge_self, merge_user
from layered_intel.models.world import WorldState, merge_world


class LLMBackend(Protocol):
    def chat_json(self, messages: list[dict], *, temperature: float = 0.1) -> dict: ...


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProfileStore:
    def __init__(self, db: Database) -> None:
        self._db = db

    def load_self(self) -> tuple[int, SelfModel]:
        row = self._db.query_one(
            "SELECT version, body FROM self_model_versions ORDER BY version DESC LIMIT 1",
            (),
        )
        if row is None:
            m = SelfModel()
            self.save_self(1, m)
            return 1, m
        return int(row["version"]), SelfModel.model_validate_json(row["body"])

    def save_self(self, version: int, model: SelfModel) -> None:
        self._db.execute(
            "INSERT INTO self_model_versions (ts, version, body) VALUES (?, ?, ?)",
            (_now(), version, model.model_dump_json()),
        )

    def load_user(self) -> tuple[int, UserModel]:
        row = self._db.query_one(
            "SELECT version, body FROM user_model_versions ORDER BY version DESC LIMIT 1",
            (),
        )
        if row is None:
            m = UserModel()
            self.save_user(1, m)
            return 1, m
        return int(row["version"]), UserModel.model_validate_json(row["body"])

    def save_user(self, version: int, model: UserModel) -> None:
        self._db.execute(
            "INSERT INTO user_model_versions (ts, version, body) VALUES (?, ?, ?)",
            (_now(), version, model.model_dump_json()),
        )

    def load_world(self) -> WorldState:
        row = self._db.query_one("SELECT body FROM world_state WHERE id = 1", ())
        if row is None:
            w = WorldState()
            self.save_world(w)
            return w
        return WorldState.model_validate_json(row["body"])

    def save_world(self, state: WorldState) -> None:
        body = state.model_dump_json()
        existing = self._db.query_one("SELECT 1 FROM world_state WHERE id = 1", ())
        if existing is None:
            self._db.execute("INSERT INTO world_state (id, body) VALUES (1, ?)", (body,))
        else:
            self._db.execute("UPDATE world_state SET body = ? WHERE id = 1", (body,))


def propose_self_patch(
    *,
    llm: LLMBackend,
    current: SelfModel,
    last_user_message: str,
    last_assistant_message: str,
) -> dict[str, Any] | None:
    messages = [
        {
            "role": "system",
            "content": (
                "You maintain a structured self-model for an assistant. "
                "Given the current JSON and the latest exchange, propose a PATCH object "
                "whose keys are ONLY top-level fields that should change. "
                "Do not include keys that are unchanged. "
                "Be conservative: small edits only. Return JSON: {\"patch\": {...}} or {\"patch\": {}}."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "current_self": current.model_dump(),
                    "last_user": last_user_message,
                    "last_assistant": last_assistant_message,
                },
                ensure_ascii=False,
            ),
        },
    ]
    data = llm.chat_json(messages, temperature=0.1)
    patch = data.get("patch")
    return patch if isinstance(patch, dict) else None


def propose_user_patch(
    *,
    llm: LLMBackend,
    current: UserModel,
    last_user_message: str,
    last_assistant_message: str,
) -> dict[str, Any] | None:
    messages = [
        {
            "role": "system",
            "content": (
                "You maintain a structured model of the user. "
                "Propose a PATCH with ONLY changed top-level fields based on the latest exchange. "
                "Never invent sensitive attributes. Return JSON {\"patch\": {...}}."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "current_user_model": current.model_dump(),
                    "last_user": last_user_message,
                    "last_assistant": last_assistant_message,
                },
                ensure_ascii=False,
            ),
        },
    ]
    data = llm.chat_json(messages, temperature=0.1)
    patch = data.get("patch")
    return patch if isinstance(patch, dict) else None


def apply_gated_self_update(current_ver: int, current: SelfModel, patch: dict[str, Any] | None) -> tuple[int, SelfModel]:
    if not patch:
        return current_ver, current
    # Gate: reject patches that add unexpected keys (merge_self already filters)
    try:
        merged = merge_self(current, patch)
    except Exception:
        return current_ver, current
    if merged.model_dump() == current.model_dump():
        return current_ver, current
    return current_ver + 1, merged


def apply_gated_user_update(current_ver: int, current: UserModel, patch: dict[str, Any] | None) -> tuple[int, UserModel]:
    if not patch:
        return current_ver, current
    try:
        merged = merge_user(current, patch)
    except Exception:
        return current_ver, current
    if merged.model_dump() == current.model_dump():
        return current_ver, current
    return current_ver + 1, merged


def update_world_from_tool(state: WorldState, tool_name: str, result: Any) -> WorldState:
    snippet = json.dumps(result, ensure_ascii=False)[:1500]
    patch = {
        "last_tool_summary": f"{tool_name}: {snippet}",
    }
    return merge_world(state, patch)

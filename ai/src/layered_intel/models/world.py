from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class WorldState(BaseModel):
    notes: str = Field(default="", max_length=4000)
    last_tool_summary: str | None = Field(default=None, max_length=4000)
    extras: dict[str, Any] = Field(default_factory=dict)


def merge_world(base: WorldState, patch: dict[str, Any]) -> WorldState:
    data = base.model_dump()
    for k, v in patch.items():
        if k in WorldState.model_fields:
            data[k] = v
    return WorldState.model_validate(data)

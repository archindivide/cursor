from __future__ import annotations

import json
from typing import Any

from layered_intel.memory.episodic import Event
from layered_intel.models.self_user import SelfModel, UserModel
from layered_intel.models.world import WorldState
from layered_intel.tools.registry import TOOL_DEFINITIONS


def build_memory_block(
    *,
    summaries: list[tuple[int, str, list[int]]],
    recent_events: list[Event],
) -> str:
    parts: list[str] = []
    if summaries:
        parts.append("## Prior summaries (with cited event ids)")
        for sid, body, cited in summaries:
            parts.append(f"- Summary #{sid} [events {cited}]: {body}")
    if recent_events:
        parts.append("## Recent episodic events (uncompressed)")
        for e in recent_events:
            tool = ""
            if e.tool_name:
                tool = f" tool={e.tool_name} args={e.tool_args} result={e.tool_result}"
            parts.append(f"- id={e.id} {e.kind} {e.role}: {e.content}{tool}")
    return "\n".join(parts) if parts else "(no episodic context yet)"


def build_system_prompt(
    *,
    self_model: SelfModel,
    user_model: UserModel,
    world: WorldState,
    memory_block: str,
) -> str:
    payload = {
        "self_model": self_model.model_dump(),
        "user_model": user_model.model_dump(),
        "world_state": world.model_dump(),
        "memory": memory_block,
        "instructions": (
            "You are a research assistant with structured memory and models of self and user. "
            "Ground answers in world_state and memory when relevant. "
            "Use tools only when needed; prefer being concise. "
            "If you use a tool, include ONE line TOOL_CALL {...} and minimal other text that turn."
        ),
        "tools_help": TOOL_DEFINITIONS,
    }
    return "Context JSON:\n" + json.dumps(payload, indent=2, ensure_ascii=False)

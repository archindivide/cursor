from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from layered_intel.agent.prompts import build_memory_block, build_system_prompt
from layered_intel.config import Settings
from layered_intel.memory.episodic import EpisodicMemory
from layered_intel.models.self_user import SelfModel, UserModel
from layered_intel.models.world import WorldState
from layered_intel.llm_base import ChatClient
from layered_intel.tools.executor import ToolExecutor, ToolResult
from layered_intel.tools.registry import parse_tool_line


@dataclass
class RouterState:
    session_id: str
    self_model: SelfModel
    user_model: UserModel
    self_version: int
    user_version: int
    world: WorldState


class Router:
    """Builds prompts from stores and runs tool-call loops until plain text remains."""

    def __init__(
        self,
        *,
        settings: Settings,
        episodic: EpisodicMemory,
        tools: ToolExecutor,
        llm: ChatClient,
    ) -> None:
        self._settings = settings
        self._episodic = episodic
        self._tools = tools
        self._llm = llm

    def _context_messages(self, state: RouterState) -> str:
        summaries = self._episodic.fetch_summaries(state.session_id)
        recent = self._episodic.fetch_recent_uncompressed(state.session_id, self._settings.recent_events_limit)
        mem = build_memory_block(summaries=summaries, recent_events=recent)
        return build_system_prompt(
            self_model=state.self_model,
            user_model=state.user_model,
            world=state.world,
            memory_block=mem,
        )

    def run_turn(self, state: RouterState, user_text: str, *, max_tool_rounds: int = 4) -> tuple[str, list[ToolResult]]:
        sys_content = self._context_messages(state)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user_text},
        ]
        tool_results: list[ToolResult] = []
        for _ in range(max_tool_rounds):
            reply = self._llm.chat(messages, temperature=0.2)
            call = _extract_tool_call(reply)
            if call is None:
                return reply.strip(), tool_results
            name, args = call
            tr = self._tools.run(name, args)
            tool_results.append(tr)
            messages.append({"role": "assistant", "content": reply})
            messages.append(
                {
                    "role": "user",
                    "content": "Tool result:\n" + __import__("json").dumps(tr.result, ensure_ascii=False),
                },
            )
        final = self._llm.chat(messages, temperature=0.2)
        return final.strip(), tool_results


_TOOL_CALL_RE = re.compile(r"^TOOL_CALL\s+\{.*\}\s*$", re.MULTILINE)


def _extract_tool_call(text: str) -> tuple[str, dict[str, Any]] | None:
    for line in text.splitlines():
        if line.strip().startswith("TOOL_CALL"):
            parsed = parse_tool_line(line)
            if parsed:
                return parsed
    # fallback: first line matching pattern
    m = _TOOL_CALL_RE.search(text)
    if m:
        parsed = parse_tool_line(m.group(0))
        if parsed:
            return parsed
    return None

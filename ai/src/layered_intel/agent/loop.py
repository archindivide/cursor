from __future__ import annotations

from dataclasses import dataclass
from layered_intel.agent.router import Router, RouterState
from layered_intel.config import Settings
from layered_intel.llm_base import ChatClient
from layered_intel.llm_client import OllamaClient
from layered_intel.memory.db import Database
from layered_intel.memory.episodic import EpisodicMemory
from layered_intel.memory.profiles import (
    ProfileStore,
    apply_gated_self_update,
    apply_gated_user_update,
    propose_self_patch,
    propose_user_patch,
    update_world_from_tool,
)
from layered_intel.memory.summaries import SummaryService
from layered_intel.tools.executor import ToolExecutor


@dataclass
class TurnResult:
    assistant_text: str


class AgentSession:
    def __init__(
        self,
        settings: Settings,
        *,
        session_id: str = "default",
        client: ChatClient | None = None,
    ) -> None:
        self.settings = settings
        self.session_id = session_id
        self._db = Database(settings.data_dir / "memory.sqlite3")
        self._episodic = EpisodicMemory(self._db)
        self._profiles = ProfileStore(self._db)
        self._summaries = SummaryService(self._db, self._episodic, batch_size=20)
        self._tools = ToolExecutor(settings.sandbox_dir)
        if client is not None:
            self._llm = client
            self._close_llm = False
        else:
            self._llm = OllamaClient(settings)
            self._close_llm = True
        self._router = Router(
            settings=settings,
            episodic=self._episodic,
            tools=self._tools,
            llm=self._llm,
        )
        sv, sm = self._profiles.load_self()
        uv, um = self._profiles.load_user()
        self._state = RouterState(
            session_id=session_id,
            self_model=sm,
            user_model=um,
            self_version=sv,
            user_version=uv,
            world=self._profiles.load_world(),
        )

    def close(self) -> None:
        if self._close_llm:
            self._llm.close()  # type: ignore[union-attr]
        self._db.close()

    def _persist_models_after_turn(self, user_text: str, assistant_text: str) -> None:
        s_patch = propose_self_patch(
            llm=self._llm,
            current=self._state.self_model,
            last_user_message=user_text,
            last_assistant_message=assistant_text,
        )
        new_sv, new_sm = apply_gated_self_update(self._state.self_version, self._state.self_model, s_patch)
        if new_sv != self._state.self_version:
            self._profiles.save_self(new_sv, new_sm)
            self._state.self_version = new_sv
            self._state.self_model = new_sm

        u_patch = propose_user_patch(
            llm=self._llm,
            current=self._state.user_model,
            last_user_message=user_text,
            last_assistant_message=assistant_text,
        )
        new_uv, new_um = apply_gated_user_update(self._state.user_version, self._state.user_model, u_patch)
        if new_uv != self._state.user_version:
            self._profiles.save_user(new_uv, new_um)
            self._state.user_version = new_uv
            self._state.user_model = new_um

    def step(self, user_text: str) -> TurnResult:
        self._episodic.append(
            session_id=self.session_id,
            role="user",
            kind="message",
            content=user_text,
        )
        assistant_text, tool_results = self._router.run_turn(self._state, user_text)
        for tr in tool_results:
            self._episodic.append(
                session_id=self.session_id,
                role="assistant",
                kind="tool",
                content=f"tool {tr.name}",
                tool_name=tr.name,
                tool_args=tr.arguments,
                tool_result=tr.result,
            )
            self._state.world = update_world_from_tool(self._state.world, tr.name, tr.result)
        self._profiles.save_world(self._state.world)
        self._episodic.append(
            session_id=self.session_id,
            role="assistant",
            kind="message",
            content=assistant_text,
        )
        self._summaries.maybe_roll_summary(
            session_id=self.session_id,
            total_uncompressed_threshold=self.settings.summarize_event_threshold,
            llm=self._llm,
        )
        self._persist_models_after_turn(user_text, assistant_text)
        return TurnResult(assistant_text=assistant_text)

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str
    model: str
    data_dir: Path
    sandbox_dir: Path
    summarize_event_threshold: int = 30
    recent_events_limit: int = 20

    @staticmethod
    def load(
        *,
        model: str,
        data_dir: Path,
        ollama_base_url: str | None = None,
        sandbox_dir: Path | None = None,
    ) -> Settings:
        base = ollama_base_url or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
        data_dir = data_dir.resolve()
        sand = sandbox_dir or Path(os.environ.get("LAYERED_SANDBOX", str(data_dir / "sandbox")))
        sand = sand.resolve()
        return Settings(
            ollama_base_url=base.rstrip("/"),
            model=model,
            data_dir=data_dir,
            sandbox_dir=sand,
        )

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from layered_intel.tools import registry as reg


@dataclass(frozen=True)
class ToolResult:
    name: str
    arguments: dict[str, Any]
    result: dict[str, Any]


class ToolExecutor:
    def __init__(self, sandbox_root: Path) -> None:
        self._root = sandbox_root
        self._root.mkdir(parents=True, exist_ok=True)

    def run(self, name: str, args: dict[str, Any]) -> ToolResult:
        out = reg.dispatch(name, args, self._root)
        return ToolResult(name=name, arguments=args, result=out)

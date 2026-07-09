from __future__ import annotations

from pathlib import Path


class SandboxViolation(Exception):
    pass


def resolve_under_sandbox(sandbox_root: Path, relative_path: str) -> Path:
    root = sandbox_root.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as e:
        raise SandboxViolation("Path escapes sandbox") from e
    return candidate

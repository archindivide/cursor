from __future__ import annotations

from pathlib import Path

import pytest

from layered_intel.tools.executor import ToolExecutor
from layered_intel.tools.sandbox import SandboxViolation, resolve_under_sandbox


def test_resolve_blocks_escape(tmp_path: Path) -> None:
    root = tmp_path / "s"
    root.mkdir()
    (root / "a.txt").write_text("hi", encoding="utf-8")
    with pytest.raises(SandboxViolation):
        resolve_under_sandbox(root, "..\\..\\outside")


def test_list_and_write_read(tmp_path: Path) -> None:
    ex = ToolExecutor(tmp_path / "sand")
    r1 = ex.run("list_sandbox", {"path": "."})
    assert r1.result["ok"] is True
    w = ex.run("write_sandbox_file", {"path": "x/hello.txt", "content": "abc"})
    assert w.result["ok"] is True
    r2 = ex.run("read_sandbox_file", {"path": "x/hello.txt"})
    assert r2.result["ok"] is True
    assert r2.result["content"] == "abc"

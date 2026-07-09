from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from layered_intel.tools.sandbox import SandboxViolation, resolve_under_sandbox

ToolName = Literal["list_sandbox", "read_sandbox_file", "write_sandbox_file"]


TOOL_DEFINITIONS = """
Available tools (call by emitting a single line exactly like):
TOOL_CALL {"name": "<name>", "arguments": <json object>}

Tools:
- list_sandbox: arguments {"path": "."} lists files relative to sandbox root.
- read_sandbox_file: arguments {"path": "relative/path.txt"}
- write_sandbox_file: arguments {"path": "relative/path.txt", "content": "..."}
""".strip()


def list_sandbox(sandbox_root: Path, path: str = ".") -> dict[str, Any]:
    base = resolve_under_sandbox(sandbox_root, path)
    if not base.exists():
        return {"ok": False, "error": "path does not exist", "path": str(path)}
    if base.is_file():
        return {"ok": True, "type": "file", "path": path}
    entries = sorted(p.name for p in base.iterdir())
    return {"ok": True, "type": "dir", "path": path, "entries": entries}


def read_sandbox_file(sandbox_root: Path, path: str) -> dict[str, Any]:
    target = resolve_under_sandbox(sandbox_root, path)
    if not target.is_file():
        return {"ok": False, "error": "not a file", "path": path}
    text = target.read_text(encoding="utf-8", errors="replace")
    return {"ok": True, "path": path, "content": text[:8000]}


def write_sandbox_file(sandbox_root: Path, path: str, content: str) -> dict[str, Any]:
    target = resolve_under_sandbox(sandbox_root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"ok": True, "path": path, "bytes": len(content.encode("utf-8"))}


def dispatch(name: str, args: dict[str, Any], sandbox_root: Path) -> dict[str, Any]:
    try:
        if name == "list_sandbox":
            return list_sandbox(sandbox_root, str(args.get("path", ".")))
        if name == "read_sandbox_file":
            p = args.get("path")
            if not isinstance(p, str):
                return {"ok": False, "error": "missing path"}
            return read_sandbox_file(sandbox_root, p)
        if name == "write_sandbox_file":
            p = args.get("path")
            if not isinstance(p, str):
                return {"ok": False, "error": "missing path"}
            return write_sandbox_file(sandbox_root, p, str(args.get("content", "")))
    except SandboxViolation as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": repr(e)}
    return {"ok": False, "error": f"unknown tool {name}"}


def parse_tool_line(line: str) -> tuple[str, dict[str, Any]] | None:
    s = line.strip()
    prefix = "TOOL_CALL"
    if not s.startswith(prefix):
        return None
    rest = s[len(prefix) :].strip()
    try:
        data = json.loads(rest)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    name = data.get("name")
    args = data.get("arguments")
    if not isinstance(name, str) or not isinstance(args, dict):
        return None
    return name, args

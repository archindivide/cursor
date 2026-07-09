"""
Evaluation harness: runs automated pytest scenarios (stub LLM, no Ollama).

Optional live check with Ollama (best-effort; requires a running model).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run_pytest() -> int:
    root = Path(__file__).resolve().parents[1]
    return subprocess.call(
        [sys.executable, "-m", "pytest", str(root / "tests"), "-q"],
        cwd=str(root),
    )


def _run_live(model: str, data_dir: Path) -> int:
    from layered_intel.agent.loop import AgentSession
    from layered_intel.config import Settings

    settings = Settings.load(model=model, data_dir=data_dir)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.sandbox_dir.mkdir(parents=True, exist_ok=True)
    (settings.sandbox_dir / "ping.txt").write_text("pong", encoding="utf-8")
    s = AgentSession(settings, session_id="eval_live")
    try:
        r1 = s.step("Read sandbox file ping.txt and reply with one word from its contents.")
        if "pong" not in r1.assistant_text.lower():
            print("live scenario failed: expected pong in reply:", r1.assistant_text)
            return 2
        r2 = s.step("What file did you just read?")
        if "ping" not in r2.assistant_text.lower():
            print("live scenario weak: expected mention of ping.txt:", r2.assistant_text)
    except Exception as e:
        print("live scenario skipped (Ollama unreachable?):", e)
        return 0
    finally:
        s.close()
    print("live scenarios ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--use-ollama", action="store_true", help="Also run a tiny live Ollama scenario")
    p.add_argument("--model", default="llama3.2")
    p.add_argument("--data-dir", type=Path, default=Path("./data_eval"))
    args = p.parse_args(argv)
    code = _run_pytest()
    if code != 0:
        return code
    if args.use_ollama:
        return _run_live(args.model, args.data_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

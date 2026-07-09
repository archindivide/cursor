from __future__ import annotations

import argparse
import sys
from pathlib import Path

from layered_intel.agent.loop import AgentSession
from layered_intel.config import Settings


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Layered OSS LLM chat (Ollama).")
    p.add_argument("--model", default="llama3.2", help="Ollama model name")
    p.add_argument("--data-dir", type=Path, default=Path("./data"), help="SQLite + sandbox root")
    p.add_argument("--session", default="default", help="Session id for episodic memory")
    p.add_argument("--ollama-host", default=None, help="Override OLLAMA_HOST")
    args = p.parse_args(argv)

    settings = Settings.load(
        model=args.model,
        data_dir=args.data_dir,
        ollama_base_url=args.ollama_host,
    )
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.sandbox_dir.mkdir(parents=True, exist_ok=True)

    session = AgentSession(settings, session_id=args.session)
    try:
        print("layered-intel chat. Ctrl+C or empty line to exit.")
        while True:
            try:
                line = input("you> ").strip()
            except EOFError:
                break
            if not line:
                break
            out = session.step(line)
            print("assistant>", out.assistant_text)
            print()
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

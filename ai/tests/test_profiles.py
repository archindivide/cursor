from __future__ import annotations

from pathlib import Path

from layered_intel.memory.db import Database
from layered_intel.memory.profiles import ProfileStore, apply_gated_self_update
from layered_intel.models.self_user import SelfModel


def test_self_version_increment(tmp_path: Path) -> None:
    db = Database(tmp_path / "p.sqlite3")
    ps = ProfileStore(db)
    v, m = ps.load_self()
    assert v == 1
    nv, nm = apply_gated_self_update(v, m, {"behavior_notes": "be brief"})
    assert nv == 2
    assert nm.behavior_notes == "be brief"
    ps.save_self(nv, nm)
    v2, m2 = ps.load_self()
    assert v2 == 2
    assert m2.behavior_notes == "be brief"

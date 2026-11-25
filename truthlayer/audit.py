"""Append-only audit log (JSON lines). Every check, finding, proposal, approval and publish."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_file(p: str | Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def log(audit_file: str | Path, action: str, item: str = "", model: str = "",
        prompt_hash: str = "", approver: str = "", **extra) -> dict:
    rec = {"time": datetime.now(timezone.utc).isoformat(timespec="seconds"), "action": action,
           "item": item, "model": model, "prompt_hash": prompt_hash, "approver": approver}
    rec.update(extra)
    p = Path(audit_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def read(audit_file: str | Path) -> list[dict]:
    p = Path(audit_file)
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

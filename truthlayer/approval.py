"""2C. Nothing is published unless APPROVED. Review, approve, reject, auto-approve HIGH."""
from __future__ import annotations

import difflib
import json

from . import audit
from .config import Config


def load(cfg: Config) -> dict:
    p = cfg.fixes_dir / "proposals.json"
    return json.loads(p.read_text())


def save(cfg: Config, data: dict):
    (cfg.fixes_dir / "proposals.json").write_text(json.dumps(data, indent=1))


def _find(data, pid):
    for p in data["proposals"]:
        if p["id"] == pid:
            return p
    raise KeyError(f"no proposal {pid}")


def set_status(cfg: Config, pid: str, status: str, approver: str) -> dict:
    data = load(cfg)
    p = _find(data, pid)
    p["status"], p["approver"] = status, approver
    save(cfg, data)
    audit.log(cfg.audit_file, "approval" if status == "APPROVED" else "rejection", item=pid,
              model=p["model"], prompt_hash=p["prompt_hash"], approver=approver)
    return p


def auto_approve_high(cfg: Config) -> list[str]:
    """Approve only HIGH-confidence proposals that actually change something. Approver is 'auto'."""
    data = load(cfg)
    done = []
    for p in data["proposals"]:
        if p["status"] == "PENDING" and p["confidence"] == "HIGH" and p["changed"] and p["publishable"]:
            p["status"], p["approver"] = "APPROVED", "auto"
            done.append(p["id"])
            audit.log(cfg.audit_file, "approval", item=p["id"], model=p["model"],
                      prompt_hash=p["prompt_hash"], approver="auto", rule="--auto-approve-high")
    save(cfg, data)
    return done


def review_text(cfg: Config, only_pending: bool = False) -> str:
    data = load(cfg)
    out = [f"Mode: {data['meta']['mode']}   Proposals: {len(data['proposals'])}", ""]
    for p in data["proposals"]:
        if only_pending and p["status"] != "PENDING":
            continue
        out.append(f"{p['id']}  [{p['status']}]  {p['label']}/{p['confidence']}  {p['element']}  ({p['file']}:{p['line']})")
        if p["changed"]:
            d = difflib.unified_diff(p["original"].split("\n"), p["proposed"].split("\n"), "before", "after", lineterm="", n=0)
            out += ["    " + l for l in list(d)[2:12]]
        else:
            out.append("    (no change proposed: " + p["reason"] + ")")
        out.append("")
    return "\n".join(out)

"""Glue: check -> fix -> approve -> publish."""
from __future__ import annotations
import time
from . import approval, audit, fixer, publisher, style
from .config import Config
from .drift import analyse, write_reports


def check(cfg: Config):
    a = analyse(cfg)
    sf = style.check_docs(cfg.docs_dir, cfg.style_rules, cfg.root) if cfg.style_rules else []
    for s in sf:
        audit.log(cfg.audit_file, "style_finding", item=f"{s['rule']} {s['file']}:{s['line']}")
    write_reports(a, cfg, sf)
    return a, sf


def run_all(cfg: Config, auto_high: bool = False) -> dict:
    t0 = time.perf_counter()
    a, sf = check(cfg)
    props = fixer.propose_fixes(a, cfg)
    auto = approval.auto_approve_high(cfg) if auto_high else []
    props = approval.load(cfg)
    manifest = publisher.publish(a, cfg, props)
    return {"seconds": round(time.perf_counter() - t0, 2), "analysis": a, "style": sf,
            "proposals": props, "auto_approved": auto, "manifest": manifest}

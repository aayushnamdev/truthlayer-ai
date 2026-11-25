"""Glue: check -> fix -> approve -> publish."""
from __future__ import annotations

import logging
import time
from typing import Any

from . import approval, audit, fixer, publisher, style
from .config import Config
from .drift import Analysis, analyse, write_reports
from .settings import Settings, load_settings

log = logging.getLogger("truthlayer.pipeline")


def check(cfg: Config) -> tuple[Analysis, list[dict[str, Any]]]:
    a = analyse(cfg)
    sf: list[dict[str, Any]] = []
    if cfg.style_rules:
        if not cfg.style_rules.exists():
            raise FileNotFoundError(f"style rules file not found: {cfg.style_rules}")
        sf = style.check_docs(cfg.docs_dir, cfg.style_rules, cfg.root)
    for s in sf:
        audit.log(cfg.audit_file, "style_finding", item=f"{s['rule']} {s['file']}:{s['line']}")
    write_reports(a, cfg, sf)
    log.info("check_done findings=%d style=%d", len(a.findings), len(sf))
    return a, sf


def run_all(cfg: Config, auto_high: bool = False, live: bool = False, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or load_settings(cfg.root)
    t0 = time.perf_counter()
    a, sf = check(cfg)
    fixer.propose_fixes(a, cfg, settings, live=live)
    auto = approval.auto_approve_high(cfg) if auto_high else []
    props = approval.load(cfg)
    manifest = publisher.publish(a, cfg, props)
    return {"seconds": round(time.perf_counter() - t0, 2), "analysis": a, "style": sf,
            "proposals": props, "auto_approved": auto, "manifest": manifest}

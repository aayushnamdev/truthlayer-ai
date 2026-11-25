"""2A/2B. Build a tiny prompt per finding, ask the AI (or the labelled MOCK) for a fix.

The AI sees ONLY the doc passage and the matching v2 element definition.
Budget rules (enforced in code): only the configured model; only CRITICAL/HIGH findings; at most
`max_calls` calls in total (retries count); a hard cost limit checked BEFORE every attempt.
The API key is read from the environment, never printed, logged or stored.
"""
from __future__ import annotations
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Callable

from . import audit
from .budget import Budget, BudgetExceeded
from .config import Config
from .drift import Analysis, EXAMPLE, GHOST, SEVERITY_RANK, WRONG, Finding
from .settings import Settings, load_settings
from .specdiff import CHANGED, REMOVED, RENAME_KINDS

log = logging.getLogger("truthlayer.fixer")

SYSTEM = ("You fix API documentation. You are given one passage from an old booklet and the current v2 "
          "definition of the element it mentions. Change ONLY the words that are wrong because of that "
          "definition. Keep everything else byte-for-byte. Reply with JSON only: "
          '{"revised_passage": "...", "reason": "..."}')


class AIUnavailable(RuntimeError):
    pass


def has_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def mode(live: bool = False) -> str:
    return "LIVE" if live and has_key() else "MOCK"


def scrub(text: str) -> str:
    """Remove the API key (if it ever shows up in an error message) before text is shown or logged."""
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key and key in text:
        text = text.replace(key, "[hidden]")
    return re.sub(r"sk-ant-[A-Za-z0-9_\-]{8,}", "[hidden]", text)


def passage_for(a: Analysis, loc: dict[str, Any], max_chars: int) -> tuple[str, int, int]:
    """Text of the block holding this location. Big sample files: +-3 lines around it."""
    b = next((x for x in a.blocks if x.id == loc["block_id"]), None)
    if b is None:
        return "", loc["line"], loc["line"]
    if b.file.endswith(".json"):
        lines = b.text.split("\n")
        lo, hi = max(1, loc["line"] - 3), min(len(lines), loc["line"] + 3)
        return "\n".join(lines[lo - 1:hi])[:max_chars], lo, hi
    return b.text[:max_chars], b.line, b.end_line


def build_prompt(passage: str, v2_def: str, detail: str, v1_name: str, v2_name: str) -> str:
    return (f"PASSAGE:\n{passage}\n\nV2 ELEMENT DEFINITION:\n{v2_def or '(element does not exist in v2)'}\n"
            f"WHAT CHANGED: {detail}\nOLD NAME IN PASSAGE: {v1_name}\nV2 NAME: {v2_name or '(none)'}\n")


def _mock_fix(f: Finding, passage: str, loc: dict[str, Any]) -> tuple[str, str]:
    """Deterministic stand-in for the AI. Only does safe, obvious edits."""
    new = f.v2_element.split(".")[-1].replace("[x]", "") if f.v2_element else ""
    tok = loc["token"]
    if f.change_kind in RENAME_KINDS and new and tok in passage:
        return passage.replace(tok, new, 1), f"MOCK: rename {tok} -> {new}"
    if f.change_kind == CHANGED and loc["kind"] in ("prose", "list_item", "table"):
        return passage + f" (v2 note: {f.detail})", "MOCK: appended a v2 note"
    if f.change_kind == REMOVED and loc["kind"] in ("prose", "list_item", "table"):
        return passage + " (removed in v2)", "MOCK: marked as removed in v2"
    return passage, "MOCK: no safe automatic edit for this case"


def _parse_reply(text: str) -> tuple[str, str]:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return "", "unparseable reply"
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return "", "unparseable reply"
    return str(d.get("revised_passage", "")), str(d.get("reason", ""))


class LiveClient:
    """One guarded way to call the API: budget check before every attempt, retries with backoff."""

    def __init__(self, settings: Settings, budget: Budget, sleep: Callable[[float], None] = time.sleep,
                 client: Any = None):
        self.s, self.budget, self.sleep = settings, budget, sleep
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            if not has_key():
                raise AIUnavailable("ANTHROPIC_API_KEY is not set")
            import anthropic
            # max_retries=0: the SDK must not retry behind our back, retries are ours and are budgeted
            self._client = anthropic.Anthropic(max_retries=0, timeout=40.0)
        return self._client

    def call(self, prompt: str, label: str) -> tuple[str, str, int, int]:
        ai = self.s.ai
        last = ""
        for attempt in range(ai.retries + 1):
            est = self.budget.estimate(len(prompt), len(SYSTEM))
            self.budget.check(est)                      # raises BudgetExceeded before any spend
            try:
                resp = self.client.messages.create(model=ai.model, max_tokens=ai.max_output_tokens, system=SYSTEM,
                                                   messages=[{"role": "user", "content": prompt}])
            except BudgetExceeded:
                raise
            except Exception as exc:                    # network, auth, rate limit, overload
                last = scrub(f"{type(exc).__name__}: {exc}")[:200]
                self.budget.charge(f"{label} (attempt {attempt + 1} failed)", None, None, est, False)
                log.warning("ai_call_failed label=%s attempt=%d error=%s", label, attempt + 1, last)
                if attempt < ai.retries:
                    self.sleep(ai.backoff_seconds * (2 ** attempt))
                    continue
                raise AIUnavailable(f"AI call failed after {attempt + 1} attempt(s): {last}") from None
            text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")
            tin, tout = int(resp.usage.input_tokens), int(resp.usage.output_tokens)
            self.budget.charge(label, tin, tout, est, True)
            revised, reason = _parse_reply(text)
            return revised, reason, tin, tout
        raise AIUnavailable(last)


def candidates(a: Analysis, settings: Settings) -> list[Finding]:
    sev = set(settings.ai.fix_severities)
    pool = [f for f in a.findings if f.label in (WRONG, EXAMPLE, GHOST) and f.severity in sev and f.locations]
    pool.sort(key=lambda f: (SEVERITY_RANK[f.severity], f.confidence != "HIGH", f.id))
    return pool


def propose_fixes(a: Analysis, cfg: Config, settings: Settings | None = None, live: bool = False,
                  client: Any = None, sleep: Callable[[float], None] = time.sleep,
                  limit_calls: int | None = None) -> dict[str, Any]:
    settings = settings or load_settings(cfg.root)
    cfg.fixes_dir.mkdir(parents=True, exist_ok=True)
    m = mode(live) if client is None else ("LIVE" if live else "MOCK")
    if live and m == "MOCK":
        log.warning("live AI requested but ANTHROPIC_API_KEY is not set; running in MOCK mode")
    budget = Budget(cfg.fixes_dir / "cost-ledger.json", settings.ai)
    start_calls = int(budget.data["calls"])
    live_client = LiveClient(settings, budget, sleep, client) if m == "LIVE" else None
    proposals: list[dict[str, Any]] = []
    stopped = ""
    for f in candidates(a, settings):
        loc = f.locations[0]                          # one small prompt per finding
        passage, lo, hi = passage_for(a, loc, settings.ai.max_passage_chars)
        if not passage:
            continue
        prompt = build_prompt(passage, f.v2_def, f.detail, f.v1_element, f.v2_element)
        ph = audit.sha256_text(prompt)
        ti = to = 0
        if live_client is not None:
            if limit_calls is not None and int(budget.data["calls"]) - start_calls >= limit_calls:
                stopped = f"stopped at the requested limit of {limit_calls} calls"
                break
            try:
                revised, reason, ti, to = live_client.call(prompt, f.id)
            except BudgetExceeded as exc:
                stopped = f"stopped before the call that would exceed the budget: {exc}"
                audit.log(cfg.audit_file, "budget_stop", item=f.id, reason=str(exc))
                break
            except AIUnavailable as exc:
                revised, reason = passage, str(exc)
        else:
            revised, reason = _mock_fix(f, passage, loc)
        if live_client is not None and not revised:
            revised = passage
        p = {"id": f"P-{len(proposals) + 1:03d}", "finding_id": f.id, "label": f.label, "severity": f.severity,
             "confidence": f.confidence, "status": "PENDING", "mode": m,
             "model": settings.ai.model if m == "LIVE" else "MOCK (no model called)",
             "file": loc["file"], "line": lo, "end_line": hi, "kind": loc["kind"],
             "element": f.v1_element, "v2_element": f.v2_element,
             "original": passage, "proposed": revised, "changed": revised.strip() != passage.strip(),
             "reason": reason, "prompt_hash": ph, "input_tokens": ti, "output_tokens": to,
             "publishable": loc["file"].endswith(".md"), "approver": ""}
        proposals.append(p)
        audit.log(cfg.audit_file, "proposal", item=p["id"], model=p["model"], prompt_hash=ph, finding=f.id, mode=m)
    data = {"meta": {"mode": m, "model": settings.ai.model if m == "LIVE" else "MOCK",
                     "input_tokens": sum(p["input_tokens"] for p in proposals),
                     "output_tokens": sum(p["output_tokens"] for p in proposals),
                     "calls_this_run": int(budget.data["calls"]) - start_calls,
                     "estimated_cost_usd": budget.real_cost_usd() if m == "LIVE" else 0.0,
                     "budget": {"limit_usd": settings.ai.cost_limit_usd, "charged_usd": round(budget.spent, 6),
                                "remaining_usd": round(budget.remaining, 6), "calls_total": budget.data["calls"],
                                "max_calls": settings.ai.max_calls},
                     "stopped": stopped,
                     "note": "MOCK mode: deterministic stand-in, no AI used, cost is 0." if m == "MOCK"
                     else "Cost uses ASSUMED per-token prices; budget charges apply a safety multiplier."},
            "proposals": proposals}
    (cfg.fixes_dir / "proposals.json").write_text(json.dumps(data, indent=1))
    return data


def ai_test(a: Analysis, cfg: Config, settings: Settings, client: Any = None) -> dict[str, Any]:
    """ONE real call on the first candidate, to see real token use before the full run."""
    cands = candidates(a, settings)
    if not cands:
        raise ValueError("no CRITICAL/HIGH findings to test with")
    f = cands[0]
    loc = f.locations[0]
    passage, _, _ = passage_for(a, loc, settings.ai.max_passage_chars)
    prompt = build_prompt(passage, f.v2_def, f.detail, f.v1_element, f.v2_element)
    budget = Budget(cfg.fixes_dir / "cost-ledger.json", settings.ai)
    lc = LiveClient(settings, budget, client=client)
    revised, reason, tin, tout = lc.call(prompt, f"test:{f.id}")
    audit.log(cfg.audit_file, "ai_test_call", item=f.id, model=settings.ai.model,
              prompt_hash=audit.sha256_text(prompt), input_tokens=tin, output_tokens=tout)
    return {"finding": f.id, "input_tokens": tin, "output_tokens": tout, "revised": revised, "reason": reason,
            "cost_usd_at_assumed_prices": round((tin * settings.ai.price_in_per_mtok + tout * settings.ai.price_out_per_mtok) / 1e6, 6),
            "budget_remaining_usd": round(budget.remaining, 6)}


def propose_one(a: Analysis, cfg: Config, settings: Settings, finding_id: str, live: bool = False,
                client: Any = None, sleep: Callable[[float], None] = time.sleep) -> dict[str, Any]:
    """Make (or replace) the proposal for ONE finding. Used by the dashboard button; same guards as the batch run."""
    f = next((x for x in a.findings if x.id == finding_id), None)
    if f is None or not f.locations:
        raise KeyError(f"no fixable finding {finding_id}")
    p_path = cfg.fixes_dir / "proposals.json"
    data = json.loads(p_path.read_text()) if p_path.exists() else {"meta": {"mode": "MOCK"}, "proposals": []}
    loc = f.locations[0]
    passage, lo, hi = passage_for(a, loc, settings.ai.max_passage_chars)
    prompt = build_prompt(passage, f.v2_def, f.detail, f.v1_element, f.v2_element)
    ph = audit.sha256_text(prompt)
    m = mode(live) if client is None else ("LIVE" if live else "MOCK")
    ti = to = 0
    if m == "LIVE":
        budget = Budget(cfg.fixes_dir / "cost-ledger.json", settings.ai)
        revised, reason, ti, to = LiveClient(settings, budget, sleep, client).call(prompt, f.id) or ("", "", 0, 0)
        revised = revised or passage
    else:
        revised, reason = _mock_fix(f, passage, loc)
    props = [x for x in data["proposals"] if x["finding_id"] != finding_id]
    pid = f"P-{len(data['proposals']) + 1:03d}"
    p = {"id": pid, "finding_id": f.id, "label": f.label, "severity": f.severity, "confidence": f.confidence,
         "status": "PENDING", "mode": m, "model": settings.ai.model if m == "LIVE" else "MOCK (no model called)",
         "file": loc["file"], "line": lo, "end_line": hi, "kind": loc["kind"], "element": f.v1_element,
         "v2_element": f.v2_element, "original": passage, "proposed": revised,
         "changed": revised.strip() != passage.strip(), "reason": reason, "prompt_hash": ph,
         "input_tokens": ti, "output_tokens": to, "publishable": loc["file"].endswith(".md"), "approver": ""}
    props.append(p)
    data["proposals"] = props
    cfg.fixes_dir.mkdir(parents=True, exist_ok=True)
    p_path.write_text(json.dumps(data, indent=1))
    audit.log(cfg.audit_file, "proposal", item=pid, model=p["model"], prompt_hash=ph, finding=f.id, mode=m)
    return p

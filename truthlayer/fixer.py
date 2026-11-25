"""2A/2B. Build a tiny prompt per finding location, ask the AI (or the labelled MOCK) for a fix.

The AI sees ONLY the doc passage and the matching v2 element definition. Nothing else.
"""
from __future__ import annotations
import hashlib, json, os, re
from pathlib import Path
from . import audit
from .config import Config
from .drift import Analysis, EXAMPLE, GHOST, WRONG, Finding
from .specdiff import CHANGED, POSSIBLE_RENAME, REMOVED

DEFAULT_MODEL = "claude-haiku-5-5"
# Assumed prices in US$ per million tokens. NOT looked up: override with env vars.
PRICE_IN = float(os.environ.get("TRUTHLAYER_PRICE_IN_PER_MTOK", "1.0"))
PRICE_OUT = float(os.environ.get("TRUTHLAYER_PRICE_OUT_PER_MTOK", "5.0"))

SYSTEM = ("You fix API documentation. You are given one passage from an old booklet and the current v2 "
          "definition of the element it mentions. Change ONLY the words that are wrong because of that "
          "definition. Keep everything else byte-for-byte. Reply with JSON only: "
          '{"revised_passage": "...", "reason": "..."}')


def mode() -> str:
    return "LIVE" if os.environ.get("ANTHROPIC_API_KEY") else "MOCK"


def model_name() -> str:
    return os.environ.get("TRUTHLAYER_MODEL", DEFAULT_MODEL)


def passage_for(a: Analysis, loc: dict, root: Path) -> tuple[str, int, int]:
    """Text of the block holding this location. Big sample files: +-3 lines around it."""
    b = next((x for x in a.blocks if x.id == loc["block_id"]), None)
    if b is None:
        return "", loc["line"], loc["line"]
    if b.file.endswith(".json"):
        lines = b.text.split("\n")
        lo, hi = max(1, loc["line"] - 3), min(len(lines), loc["line"] + 3)
        return "\n".join(lines[lo - 1:hi]), lo, hi
    return b.text[:1500], b.line, b.end_line


def build_prompt(passage: str, v2_def: str, detail: str, v1_name: str, v2_name: str) -> str:
    return (f"PASSAGE:\n{passage}\n\nV2 ELEMENT DEFINITION:\n{v2_def or '(element does not exist in v2)'}\n"
            f"WHAT CHANGED: {detail}\nOLD NAME IN PASSAGE: {v1_name}\nV2 NAME: {v2_name or '(none)'}\n")


def _mock_fix(f: Finding, passage: str, loc: dict) -> tuple[str, str]:
    """Deterministic stand-in for the AI. Only does safe, obvious edits."""
    old = f.v1_element.split(".")[-1].replace("[x]", "")
    new = f.v2_element.split(".")[-1].replace("[x]", "") if f.v2_element else ""
    tok = loc["token"]
    if f.change_kind == POSSIBLE_RENAME and new and tok in passage:
        return passage.replace(tok, new, 1), f"MOCK: guessed rename {tok} -> {new}"
    if f.change_kind == CHANGED and loc["kind"] in ("prose", "list_item", "table"):
        return passage + f" (v2 note: {f.detail})", "MOCK: appended a v2 note"
    if f.change_kind == REMOVED and loc["kind"] in ("prose", "list_item", "table"):
        return passage + " (removed in v2)", "MOCK: marked as removed in v2"
    return passage, "MOCK: no safe automatic edit for this case"


def _live_fix(prompt: str) -> tuple[str, str, int, int]:
    import anthropic
    client = anthropic.Anthropic()
    resp = client.messages.create(model=model_name(), max_tokens=900, system=SYSTEM,
                                  messages=[{"role": "user", "content": prompt}])
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    m = re.search(r"\{.*\}", text, re.S)
    data = json.loads(m.group(0)) if m else {"revised_passage": "", "reason": "unparseable reply"}
    return data.get("revised_passage", ""), data.get("reason", ""), resp.usage.input_tokens, resp.usage.output_tokens


def propose_fixes(a: Analysis, cfg: Config) -> dict:
    cfg.fixes_dir.mkdir(parents=True, exist_ok=True)
    m = mode()
    proposals = []
    totals = {"input_tokens": 0, "output_tokens": 0}
    seen_blocks: set[tuple] = set()
    for f in a.findings:
        if f.label not in (WRONG, EXAMPLE, GHOST):
            continue
        for loc in f.locations:
            key = (f.id, loc["block_id"])
            if key in seen_blocks:
                continue
            seen_blocks.add(key)
            passage, lo, hi = passage_for(a, loc, cfg.root)
            if not passage:
                continue
            prompt = build_prompt(passage, f.v2_def, f.detail, f.v1_element, f.v2_element)
            ph = audit.sha256_text(prompt)
            if m == "LIVE":
                try:
                    revised, reason, ti, to = _live_fix(prompt)
                except Exception as e:      # network / auth problems must not crash the run
                    revised, reason, ti, to = passage, f"AI call failed: {e}", 0, 0
            else:
                revised, reason = _mock_fix(f, passage, loc)
                ti = to = 0
            totals["input_tokens"] += ti
            totals["output_tokens"] += to
            p = {"id": f"P-{len(proposals)+1:03d}", "finding_id": f.id, "label": f.label,
                 "confidence": f.confidence, "status": "PENDING", "mode": m,
                 "model": model_name() if m == "LIVE" else "MOCK (no model called)",
                 "file": loc["file"], "line": lo, "end_line": hi, "kind": loc["kind"],
                 "element": f.v1_element, "v2_element": f.v2_element,
                 "original": passage, "proposed": revised, "changed": revised.strip() != passage.strip(),
                 "reason": reason, "prompt_hash": ph, "input_tokens": ti, "output_tokens": to,
                 "publishable": loc["file"].endswith(".md"), "approver": ""}
            proposals.append(p)
            audit.log(cfg.audit_file, "proposal", item=p["id"], model=p["model"], prompt_hash=ph,
                      finding=f.id, mode=m)
    cost = (totals["input_tokens"] * PRICE_IN + totals["output_tokens"] * PRICE_OUT) / 1e6
    data = {"meta": {"mode": m, "model": model_name() if m == "LIVE" else "MOCK",
                     **totals, "estimated_cost_usd": round(cost, 6),
                     "price_assumption_usd_per_mtok": {"input": PRICE_IN, "output": PRICE_OUT},
                     "note": "MOCK mode: deterministic stand-in, no AI used, cost is 0." if m == "MOCK"
                     else "Cost is an estimate from assumed per-token prices."},
            "proposals": proposals}
    (cfg.fixes_dir / "proposals.json").write_text(json.dumps(data, indent=1))
    return data

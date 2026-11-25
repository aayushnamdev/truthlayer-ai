"""Plain functions behind the dashboard, so they can be tested without a browser."""
from __future__ import annotations

import difflib
import html
import json
from pathlib import Path
from typing import Any

SEVERITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
LABELS = ["WRONG", "GHOST", "EXAMPLE", "NEEDS_NOTE", "MISSING", "UNVERIFIABLE"]
SEV_COLOR = {"CRITICAL": "#b42318", "HIGH": "#c4320a", "MEDIUM": "#b54708", "LOW": "#475467"}


def load_report(reports_dir: Path) -> dict[str, Any] | None:
    p = Path(reports_dir) / "drift-report.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        return None


def filter_findings(findings: list[dict[str, Any]], severities: list[str] | None = None,
                    labels: list[str] | None = None, query: str = "") -> list[dict[str, Any]]:
    q = query.strip().lower()
    out = []
    for f in findings:
        if severities and f["severity"] not in severities:
            continue
        if labels and f["label"] not in labels:
            continue
        if q and q not in (f["v1_element"] + " " + f["v2_element"] + " " + f["detail"]).lower():
            continue
        out.append(f)
    rank = {s: i for i, s in enumerate(SEVERITIES)}
    return sorted(out, key=lambda f: (rank.get(f["severity"], 9), f["confidence"] != "HIGH", f["id"]))


def score_cards(report: dict[str, Any], score: dict[str, Any] | None, run_seconds: float | None,
                ai_cost: float | None) -> dict[str, Any]:
    s = report["summary"]
    real = sum(1 for f in report["findings"] if f["label"] != "UNVERIFIABLE")
    return {"by_severity": {k: s["by_severity"].get(k, 0) for k in SEVERITIES},
            "cms_recall": (f"{score['caught']}/{score['n']}" if score else "n/a"),
            "cms_recall_pct": (round(100 * score["caught"] / score["n"]) if score and score.get("n") else None),
            "real_drift_found": real, "run_seconds": run_seconds, "ai_cost_usd": ai_cost}


def mark_diff(old: str, new: str) -> tuple[str, str]:
    """Two HTML strings with the differing words highlighted (red in old, green in new)."""
    a, b = old.split(), new.split()
    sm = difflib.SequenceMatcher(None, a, b)
    ha, hb = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        ta, tb = html.escape(" ".join(a[i1:i2])), html.escape(" ".join(b[j1:j2]))
        if tag == "equal":
            ha.append(ta); hb.append(tb)
        else:
            if ta:
                ha.append(f'<mark style="background:#fecdca">{ta}</mark>')
            if tb:
                hb.append(f'<mark style="background:#abefc6">{tb}</mark>')
    return " ".join(ha), " ".join(hb)


def highlight_tokens(text: str, tokens: list[str], color: str = "#fedf89") -> str:
    out = html.escape(text)
    for t in sorted({t for t in tokens if t}, key=len, reverse=True):
        et = html.escape(t)
        out = out.replace(et, f'<mark style="background:{color}">{et}</mark>')
    return out


def booklet_context(root: Path, loc: dict[str, Any], radius: int = 3) -> tuple[str, int]:
    """Lines of the booklet file around a location, so the user sees the old text in place."""
    p = Path(root) / loc["file"]
    if not p.exists():
        return loc.get("text", ""), loc["line"]
    lines = p.read_text(encoding="utf-8").split("\n")
    lo, hi = max(1, loc["line"] - radius), min(len(lines), loc["line"] + radius)
    return "\n".join(lines[lo - 1:hi]), lo


def read_audit(audit_file: Path, action: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
    p = Path(audit_file)
    if not p.exists():
        return []
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    if action:
        rows = [r for r in rows if r.get("action") == action]
    return rows[-limit:][::-1]


def zip_pages(publish_dir: Path) -> bytes:
    import io
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted((Path(publish_dir) / "pages").glob("*.md")):
            z.write(f, f"pages/{f.name}")
        for n in ("llms.txt", "llms-full.txt", "manifest.json"):
            if (Path(publish_dir) / n).exists():
                z.write(Path(publish_dir) / n, n)
    return buf.getvalue()


# The three scores against CMS's 35 listed changes (source files: reports/results.md, results-v2.md, results-v3.md).
SCORE_HISTORY = [
    {"name": "First score", "blind": True, "caught": 21, "of": 35, "note": "taken before looking at the CMS list; tool tuned only on the definitions and fixtures", "file": "reports/results.md"},
    {"name": "Second score", "blind": False, "caught": 32, "of": 35, "note": "after improving the tool on the known misses (rules, profiles, official renames)", "file": "reports/results-v2.md"},
    {"name": "Third score", "blind": False, "caught": 32, "of": 35, "note": "same recall; WRONG split into WRONG and NEEDS_NOTE", "file": "reports/results-v3.md"},
]


def ledger_summary(ledger: dict[str, Any] | None, price_in: float = 1.0, price_out: float = 5.0) -> dict[str, Any]:
    """AI use so far, from the cost ledger. Cost uses the ASSUMED prices in truthlayer.yml."""
    if not ledger:
        return {"calls": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
    tin, tout = int(ledger.get("input_tokens", 0)), int(ledger.get("output_tokens", 0))
    return {"calls": int(ledger.get("calls", 0)), "input_tokens": tin, "output_tokens": tout,
            "cost_usd": round((tin * price_in + tout * price_out) / 1e6, 4)}


def password_required(secrets: Any) -> str | None:
    """The APP_PASSWORD secret, if one is set (None means: no password gate)."""
    try:
        pw = secrets.get("APP_PASSWORD")
    except Exception:           # no secrets file at all
        return None
    return str(pw) if pw else None


def password_ok(entered: str, expected: str) -> bool:
    import hmac
    return hmac.compare_digest(entered.encode(), expected.encode())

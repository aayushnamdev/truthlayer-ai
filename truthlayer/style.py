"""1E. Apply the client style rules (rules/healthplan-style.yml). Simple regex + structure checks."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from .docmap import Block, parse_markdown

SUGGEST = {
    "HP-001": 'Say "member" instead of "patient" in prose.',
    "HP-002": "Write dates as YYYY-MM-DD.",
    "HP-003": "State the API version (for example 'API version 2') near the top.",
    "HP-004": "Add the error codes (4xx/5xx) this endpoint can return.",
    "HP-005": "Add a code sample to this endpoint section.",
    "HP-006": 'Write "ID" in capitals.',
    "HP-007": "Use descriptive link text instead of 'click here'.",
    "HP-008": "Use sentence case in headings.",
    "HP-009": "Write HTTP methods in capitals (GET, POST).",
    "HP-010": "State the FHIR version (STU3 or R4) this page follows.",
    "HP-011": 'Label example records as "synthetic" or "sandbox".',
}


def load_rules(p: Path) -> list[dict]:
    d = yaml.safe_load(Path(p).read_text())
    return d["rules"]


def _is_endpoint_heading(h: str) -> bool:
    return bool(re.search(r"(^|\s)(GET|POST|PUT|DELETE)\b|/(v\d/)?fhir/|/[A-Za-z]+\?", h))


def check_file(path: Path, rules: list[dict], display: str | None = None) -> list[dict]:
    name = display or str(path)
    text = Path(path).read_text(encoding="utf-8")
    lines = text.split("\n")
    blocks = parse_markdown(Path(path), name)
    out: list[dict] = []

    def add(rule, line, snippet=""):
        out.append({"rule": rule["id"], "name": rule["name"], "severity": rule.get("severity", "warning"),
                    "file": name, "line": line, "snippet": snippet[:120], "suggestion": SUGGEST.get(rule["id"], "")})

    for r in rules:
        kind = r.get("check")
        scope = r.get("scope", "")
        if kind == "regex":
            if "require" in r:
                hay = "\n".join(lines[:50]) if scope == "first_50_lines" else text
                if not re.search(r["require"], hay):
                    add(r, 1)
                continue
            pat = r.get("forbid") or r.get("pattern") or ""
            rx = re.compile(pat, re.M)
            if scope == "prose":
                for b in blocks:
                    if b.kind not in ("prose", "list_item"):
                        continue
                    clean = re.sub(r"`[^`]*`|\[[^\]]*\]\([^)]*\)|https?://\S+|<[^>]+>", " ", b.text)
                    m = rx.search(clean)
                    if m:
                        add(r, b.line, m.group(0))
            else:
                in_fence = False
                for i, l in enumerate(lines, 1):
                    if l.strip().startswith("```"):
                        in_fence = not in_fence
                        continue
                    if in_fence or l.lstrip().startswith(("<!--", "Source:", "Snapshot:")):
                        continue      # skip code blocks and the provenance header lines
                    m = rx.search(l)
                    if m:
                        add(r, i, l.strip())
        elif kind == "structure":
            if r["id"] in ("HP-004", "HP-005"):
                # sections = group blocks by their heading chain
                secs: dict[str, list[Block]] = {}
                for b in blocks:
                    secs.setdefault(b.section, []).append(b)
                for sec, bl in secs.items():
                    last = sec.split(" > ")[-1] if sec else ""
                    if not _is_endpoint_heading(last):
                        continue
                    body = "\n".join(b.text for b in bl)
                    line = bl[0].line
                    if r["id"] == "HP-004" and not re.search(r"\b[45]\d\d\b", body):
                        add(r, line, last)
                    if r["id"] == "HP-005" and not any(b.kind in ("sample", "code") for b in bl):
                        add(r, line, last)
            elif r["id"] == "HP-011":
                if re.search(r'"resourceType"', text) and not re.search(r"(?i)synthetic|sandbox", text):
                    add(r, 1)
    return out


def check_docs(docs_dir: Path, rules_path: Path, root: Path = Path(".")) -> list[dict]:
    rules = load_rules(rules_path)
    out = []
    for f in sorted(Path(docs_dir).glob("*.md")):
        disp = str(f.relative_to(root)) if f.is_relative_to(root) else str(f)
        out += check_file(f, rules, disp)
    return out

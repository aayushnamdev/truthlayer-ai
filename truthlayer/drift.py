"""1D. Label each piece of drift: WRONG, EXAMPLE, MISSING or GHOST. Deterministic.

WRONG   the booklet's prose/table names something that still exists but changed or was probably renamed.
EXAMPLE the old name only appears inside a sample (JSON / code), not in prose.
MISSING something changed or is new in v2 and the booklet never mentions it.
GHOST   the booklet describes something that is gone in v2 with no replacement.
"""
from __future__ import annotations
import json
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from . import audit
from .config import Config
from .docmap import (Block, Index, Mention, find_mentions, parse_json_sample, parse_markdown,
                     PROSE_KINDS, SAMPLE_KINDS)
from .fhir_adapter import load_capability, load_definitions, load_types
from .specdiff import (ADDED, CHANGED, POSSIBLE_RENAME, REMOVED, SpecChange, run_diff)

WRONG, EXAMPLE, MISSING, GHOST = "WRONG", "EXAMPLE", "MISSING", "GHOST"


@dataclass
class Finding:
    id: str
    label: str
    confidence: str            # HIGH | LOW
    ask_human: bool
    change_id: str
    change_kind: str
    category: str
    resource: str
    v1_element: str
    v2_element: str
    detail: str
    v1_def: str
    v2_def: str
    locations: list[dict] = field(default_factory=list)
    why_confidence: str = ""
    plain_english: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class Analysis:
    changes: list[SpecChange]
    blocks: list[Block]
    mentions: list[Mention]
    findings: list[Finding]
    v1_elements: dict
    v2_elements: dict


def _loc(m: Mention) -> dict:
    return {"file": m.file, "line": m.line, "section": m.section, "kind": m.kind, "token": m.token,
            "block_id": m.block_id, "ambiguous": m.ambiguous, "text": m.text}


def load_blocks(cfg: Config):
    blocks: list[Block] = []
    titles: dict[str, str] = {}
    keys: dict[str, list] = {}
    for f in sorted(Path(cfg.docs_dir).glob("*.md")):
        disp = str(f.relative_to(cfg.root)) if f.is_relative_to(cfg.root) else str(f)
        bl = parse_markdown(f, disp)
        blocks += bl
        first = next((b for b in bl if b.section), None)
        titles[disp] = first.section.split(" > ")[0] if first else f.stem
        # title: use the file name too, it names the resource ("explanation-of-benefits")
        titles[disp] = titles[disp] + " " + f.stem.replace("-", " ")
    for f in cfg.samples:
        disp = str(f.relative_to(cfg.root)) if f.is_relative_to(cfg.root) else str(f)
        blocks.append(parse_json_sample(f, disp))
        titles[disp] = f.stem.replace("-", " ")
    return blocks, titles, keys


def _prefix(path: str, anc: str) -> bool:
    return path == anc or path.startswith(anc + ".")


def analyse(cfg: Config) -> Analysis:
    v1 = load_definitions(cfg.defs_v1)
    v2 = load_definitions(cfg.defs_v2)
    c1, c2 = load_capability(cfg.cap_v1), load_capability(cfg.cap_v2)
    t1, t2 = load_types(cfg.types_v1), load_types(cfg.types_v2)
    changes = run_diff(v1, v2, c1, c2)
    audit.log(cfg.audit_file, "check_spec_diff", item=f"{len(changes)} changes", v1=len(v1), v2=len(v2))
    # resource types that exist in v1 but not in v2 (e.g. dropped between releases)
    gone_types = (t1 - t2) if t1 and t2 else set()
    idx = Index(v1, {r: d["search"] for r, d in c1.resources.items()}, gone_types)
    blocks, titles, keys = load_blocks(cfg)
    mentions = find_mentions(blocks, idx, titles)
    audit.log(cfg.audit_file, "check_docs_map", item=f"{len(blocks)} blocks, {len(mentions)} mentions")

    # resource-type "changes": v1 type missing from v2
    extra = [SpecChange(f"SC-T{n:02d}", REMOVED, "resource", g, g, "", "resource type does not exist in the v2 release")
             for n, g in enumerate(sorted(gone_types & {m.candidates[0] for m in mentions if m.category == 'resource'}), 1)]
    changes = changes + extra

    findings: list[Finding] = []
    both_caps = lambda r: r in c1.resources and r in c2.resources

    def matching(ch: SpecChange):
        out = []
        for m in mentions:
            for c in m.candidates:
                if ch.category == "element" and m.category == "element" and ch.v1_path and _prefix(c, ch.v1_path):
                    out.append(m); break
                if ch.category in ("search_param", "resource") and ch.v1_path and c == ch.v1_path and m.category == ch.category:
                    out.append(m); break
        return out

    n = 0
    for ch in changes:
        ms = matching(ch) if ch.v1_path else []
        prose = [m for m in ms if m.kind in PROSE_KINDS]
        sample = [m for m in ms if m.kind in SAMPLE_KINDS]
        label = None
        locs = ms
        if ms:
            if ch.kind == REMOVED and ch.category != "interaction":
                label = GHOST if prose else EXAMPLE
            elif ch.kind in (CHANGED, POSSIBLE_RENAME):
                label = WRONG if prose else EXAMPLE
            if ch.kind == REMOVED and sample and not prose:
                label = EXAMPLE
        else:
            if (ch.kind == ADDED and ch.category == "element") or (ch.kind == CHANGED and ch.category == "element"):
                label = MISSING
            elif ch.kind == POSSIBLE_RENAME:
                label = MISSING          # old name not mentioned, but the new name is not either
            elif ch.kind == ADDED and ch.category in ("search_param", "resource"):
                label = MISSING
        if not label:
            continue
        n += 1
        v2path = ch.v2_path
        ambiguous = any(m.ambiguous for m in ms)
        v2e = v2.get(v2path) if v2path else None
        # confidence: definitions and capability statements agree
        if ch.kind == POSSIBLE_RENAME:
            conf, why = "LOW", "possible rename guessed from similar names; needs a human check"
        elif ambiguous:
            conf, why = "LOW", "the booklet's wording matches more than one element"
        elif label == MISSING:
            if ch.category == "element" and v2e is not None and v2e.min >= 1 and both_caps(ch.resource):
                conf, why = "HIGH", "v2 definition makes it required (min>=1) and both capability statements list the resource"
            elif ch.category == "search_param":
                conf, why = "HIGH", "search parameter listed by v2 capability statement only"
            else:
                conf, why = "LOW", "optional element; whether the booklet should mention it is a human call"
        elif ch.category == "element" and both_caps(ch.resource):
            conf, why = "HIGH", "v1/v2 definitions differ and both capability statements list the resource"
        elif ch.category in ("search_param", "resource"):
            conf, why = "HIGH", "v1 capability/resource list has it and v2 does not"
        else:
            conf, why = "LOW", "resource not listed by both capability statements"
        f = Finding(f"F-{n:03d}", label, conf, conf == "LOW", ch.id, ch.kind, ch.category, ch.resource,
                    ch.v1_path, ch.v2_path, ch.detail, ch.v1_def, ch.v2_def,
                    [_loc(m) for m in locs], why)
        f.plain_english = _english(f)
        findings.append(f)
        audit.log(cfg.audit_file, "finding", item=f.id, label=label, confidence=conf,
                  element=ch.v1_path or ch.v2_path)
    return Analysis(changes, blocks, mentions, findings, v1, v2)


def _english(f: Finding) -> str:
    where = f"{f.locations[0]['file']}:{f.locations[0]['line']}" if f.locations else "nowhere"
    old, new = f.v1_element, f.v2_element
    if f.label == WRONG and f.change_kind == POSSIBLE_RENAME:
        return f"The old booklet talks about `{old}` ({where}). In v2 it may now be `{new}` - a human should confirm."
    if f.label == WRONG:
        return f"The old booklet describes `{old}` ({where}), but in v2 it changed: {f.detail}."
    if f.label == GHOST:
        return f"The old booklet describes `{old}` ({where}), which does not exist in v2 ({f.detail})."
    if f.label == EXAMPLE:
        return f"A sample in the old booklet ({where}) shows `{old}`, which v2 changed or removed ({f.detail})."
    return f"v2 {('adds' if f.change_kind == ADDED else 'changes')} `{new or old}` ({f.detail}), and the booklet never mentions it."


def write_reports(a: Analysis, cfg: Config, style_findings: list | None = None) -> tuple[Path, Path]:
    cfg.reports_dir.mkdir(parents=True, exist_ok=True)
    by = defaultdict(list)
    for f in a.findings:
        by[f.label].append(f)
    conf = defaultdict(int)
    for f in a.findings:
        conf[f.confidence] += 1
    data = {
        "summary": {"findings": len(a.findings), "by_label": {k: len(v) for k, v in by.items()},
                    "by_confidence": dict(conf), "spec_changes": len(a.changes),
                    "blocks_scanned": len(a.blocks), "mentions_found": len(a.mentions),
                    "style_findings": len(style_findings or [])},
        "spec_changes": [c.to_dict() for c in a.changes],
        "findings": [f.to_dict() for f in a.findings],
        "style_findings": style_findings or [],
    }
    jp = cfg.reports_dir / "drift-report.json"
    jp.write_text(json.dumps(data, indent=1))
    s = data["summary"]
    md = ["# Drift report", "",
          "## In plain English", "",
          f"We compared the old v1 booklet with the v1 and v2 API definitions. We found **{s['findings']} places where the booklet may be out of date** "
          f"({s['by_label'].get(WRONG, 0)} wrong, {s['by_label'].get(GHOST, 0)} describing things that no longer exist, "
          f"{s['by_label'].get(EXAMPLE, 0)} in examples only, {s['by_label'].get(MISSING, 0)} things v2 has that the booklet never mentions). "
          f"{conf.get('HIGH', 0)} are high confidence; {conf.get('LOW', 0)} are marked \"ask a human\".", "",
          "- **WRONG**: the text names something that still exists in v2 but changed (or was probably renamed).",
          "- **GHOST**: the text describes something that is gone in v2.",
          "- **EXAMPLE**: only a sample/code block shows the old name; the prose does not.",
          "- **MISSING**: v2 adds or changes it and the booklet is silent.", "",
          f"Scanned {s['blocks_scanned']} pieces of the booklet, found {s['mentions_found']} element mentions, "
          f"and compared {s['spec_changes']} differences between the v1 and v2 definitions.",
          f"Style check: {s['style_findings']} findings (see JSON).", ""]
    for label in (WRONG, GHOST, EXAMPLE, MISSING):
        fs = by.get(label, [])
        md += [f"## {label} ({len(fs)})", ""]
        if not fs:
            md += ["None.", ""]
            continue
        cap = 40 if label == MISSING else len(fs)
        md += ["| ID | Confidence | Element (v1 → v2) | Where | What |", "|---|---|---|---|---|"]
        for f in fs[:cap]:
            w = f"{f.locations[0]['file']}:{f.locations[0]['line']}" if f.locations else "-"
            md.append(f"| {f.id} | {f.confidence}{' (ask a human)' if f.ask_human else ''} | `{f.v1_element or '-'}` → `{f.v2_element or '-'}` | {w} | {f.detail} |")
        if len(fs) > cap:
            md.append(f"\n_{len(fs) - cap} more in drift-report.json._")
        md.append("")
    mp = cfg.reports_dir / "drift-report.md"
    mp.write_text("\n".join(md) + "\n")
    audit.log(cfg.audit_file, "report_written", item=str(mp))
    return mp, jp

"""1D + A1/A3/A4/A6. Label each piece of drift and give it a severity. Deterministic.

Labels
  WRONG         the booklet's text names something that still exists but changed (or was renamed).
  GHOST         the text describes something that is gone in v2 with no replacement.
  EXAMPLE       the old name only appears inside a sample (JSON / code), not in prose.
  MISSING       something changed or is new in v2 and the booklet never mentions it.
  UNVERIFIABLE  a statement no spec can prove (HTTP headers, policies); a human must check it.

Severity
  CRITICAL  breaking: removed, renamed or now-required items named in booklet text; ghost resources.
  HIGH      wrong examples; value-set, rule, type or target changes named in text.
  MEDIUM    missing required or important new items; headers a human should check.
  LOW       missing optional additions.
"""
from __future__ import annotations
import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import audit
from .config import Config
from .docmap import Block, Index, Mention, PROSE_KINDS, SAMPLE_KINDS, find_mentions, parse_json_sample, parse_markdown
from .fhir_adapter import (Element, apply_profiles, load_capability, load_definitions, load_maps,
                           load_profile_overlay, load_types)
from .specdiff import ADDED, CHANGED, POSSIBLE_RENAME, REMOVED, RENAME_KINDS, SpecChange, run_diff
from .unverifiable import find_unverifiable

log = logging.getLogger("truthlayer.drift")

WRONG, EXAMPLE, MISSING, GHOST, UNVERIFIABLE = "WRONG", "EXAMPLE", "MISSING", "GHOST", "UNVERIFIABLE"
CRITICAL, HIGH, MEDIUM, LOW = "CRITICAL", "HIGH", "MEDIUM", "LOW"
SEVERITY_RANK = {CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3}
RULE_KINDS = {"value_set", "binding_strength", "fixed_default", "target_type", "slicing", "type", "cardinality"}


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
    severity: str = LOW
    why_severity: str = ""
    sub_kinds: list[str] = field(default_factory=list)
    children: list[str] = field(default_factory=list)
    children_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Analysis:
    changes: list[SpecChange]
    blocks: list[Block]
    mentions: list[Mention]
    findings: list[Finding]
    v1_elements: dict[str, Element]
    v2_elements: dict[str, Element]


def _loc(m: Mention) -> dict[str, Any]:
    return {"file": m.file, "line": m.line, "section": m.section, "kind": m.kind, "token": m.token,
            "block_id": m.block_id, "ambiguous": m.ambiguous, "text": m.text, "evidence": m.evidence}


def load_blocks(cfg: Config) -> tuple[list[Block], dict[str, str]]:
    if not Path(cfg.docs_dir).is_dir():
        raise FileNotFoundError(f"docs folder not found: {cfg.docs_dir}")
    blocks: list[Block] = []
    titles: dict[str, str] = {}
    files = sorted(Path(cfg.docs_dir).glob("*.md"))
    if not files:
        raise ValueError(f"no .md files in docs folder {cfg.docs_dir}")
    for f in files:
        disp = str(f.relative_to(cfg.root)) if f.is_relative_to(cfg.root) else str(f)
        bl = parse_markdown(f, disp)
        blocks += bl
        first = next((b for b in bl if b.section), None)
        titles[disp] = (first.section.split(" > ")[0] if first else f.stem) + " " + f.stem.replace("-", " ")
    for f in cfg.samples:
        disp = str(f.relative_to(cfg.root)) if f.is_relative_to(cfg.root) else str(f)
        try:
            json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            log.warning("skipping sample %s: %s", f, exc)
            continue
        blocks.append(parse_json_sample(f, disp))
        titles[disp] = f.stem.replace("-", " ")
    return blocks, titles


def _prefix(path: str, anc: str) -> bool:
    return path == anc or path.startswith(anc + ".")


def _severity(label: str, ch: SpecChange, v2: dict[str, Element]) -> tuple[str, str]:
    sk = set(ch.sub_kinds)
    if label in (WRONG, GHOST):
        if ch.kind in (REMOVED, *RENAME_KINDS):
            return CRITICAL, "the text names something that was removed or renamed"
        if ch.category in ("resource", "search_param"):
            return CRITICAL, "the text describes a resource or search option that is gone"
        if "now_required" in sk:
            return CRITICAL, "the text names something that is now required"
        if sk & RULE_KINDS:
            return HIGH, "the text names something whose rules changed (" + ", ".join(sorted(sk & RULE_KINDS)) + ")"
        return MEDIUM, "the text names something that changed in a minor way"
    if label == EXAMPLE:
        if sk and sk <= {"must_support", "value_set_version"}:
            return MEDIUM, "a sample is only affected by a minor profile flag"
        return HIGH, "a sample shows the old shape"
    # MISSING
    v2e = v2.get(ch.v2_path) if ch.v2_path else None
    kids_required = any((v2.get(c) is not None and v2[c].min >= 1) for c in ch.children)
    if ch.category in ("search_param", "resource"):
        return MEDIUM, "new search option or resource in v2"
    if "now_required" in sk or (v2e is not None and v2e.min >= 1) or kids_required or "required slices" in (v2e.slicing if v2e else ""):
        return MEDIUM, "v2 requires it and the booklet is silent"
    return LOW, "optional addition or minor rule change; booklet is silent"


def analyse(cfg: Config) -> Analysis:
    v1 = apply_profiles(load_definitions(cfg.defs_v1), load_profile_overlay(cfg.profiles_v1))
    v2 = apply_profiles(load_definitions(cfg.defs_v2), load_profile_overlay(cfg.profiles_v2))
    if not v1 or not v2:
        raise ValueError("no elements found in the v1/v2 definition files")
    c1, c2 = load_capability(cfg.cap_v1), load_capability(cfg.cap_v2)
    t1, t2 = load_types(cfg.types_v1), load_types(cfg.types_v2)
    renames = load_maps(cfg.map_files)
    changes = run_diff(v1, v2, c1, c2, renames)
    audit.log(cfg.audit_file, "check_spec_diff", item=f"{len(changes)} changes", v1=len(v1), v2=len(v2),
              official_renames=len(renames))
    gone_types = (t1 - t2) if t1 and t2 else set()
    idx = Index(v1, {r: d["search"] for r, d in c1.resources.items()}, gone_types)
    blocks, titles = load_blocks(cfg)
    mentions = find_mentions(blocks, idx, titles)
    audit.log(cfg.audit_file, "check_docs_map", item=f"{len(blocks)} blocks, {len(mentions)} mentions")

    changes = changes + [
        SpecChange(f"SC-T{n:02d}", REMOVED, "resource", g, g, "", "resource type does not exist in the v2 release")
        for n, g in enumerate(sorted(gone_types & {m.candidates[0] for m in mentions if m.category == "resource"}), 1)]

    findings: list[Finding] = []
    both_caps = lambda r: r in c1.resources and r in c2.resources  # noqa: E731

    def matching(ch: SpecChange) -> list[Mention]:
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
        label = None
        if ms:
            if ch.kind == REMOVED and ch.category != "interaction":
                label = GHOST if prose else EXAMPLE
            elif ch.kind == CHANGED or ch.kind in RENAME_KINDS:
                label = WRONG if prose else EXAMPLE
        else:
            only_version = bool(ch.sub_kinds) and set(ch.sub_kinds) <= {"value_set_version"}
            if ch.category == "element" and ch.kind in (ADDED, CHANGED, *RENAME_KINDS) and not only_version:
                label = MISSING
            elif ch.kind == ADDED and ch.category in ("search_param", "resource"):
                label = MISSING
        if not label:
            continue
        n += 1
        v2e = v2.get(ch.v2_path) if ch.v2_path else None
        ambiguous = any(m.ambiguous for m in ms)
        guess_only = bool(ms) and all(m.evidence == "named_in_context" for m in ms)
        if ch.kind == POSSIBLE_RENAME:
            conf, why = "LOW", "possible rename guessed from similar names; needs a human check"
        elif ambiguous:
            conf, why = "LOW", "the booklet's wording matches more than one element"
        elif guess_only:
            conf, why = "LOW", "the booklet only names the element loosely; its resource is only named nearby"
        elif label == MISSING:
            if ch.category == "element" and v2e is not None and v2e.min >= 1 and both_caps(ch.resource):
                conf, why = "HIGH", "v2 definition makes it required (min>=1) and both capability statements list the resource"
            elif ch.category == "search_param":
                conf, why = "HIGH", "search parameter listed by v2 capability statement only"
            else:
                conf, why = "LOW", "optional element; whether the booklet should mention it is a human call"
        elif ch.kind == RENAMED_KIND:
            conf, why = "HIGH", "HL7's official R3-R4 map confirms the rename"
        elif ch.category == "element" and both_caps(ch.resource):
            conf, why = "HIGH", "v1/v2 definitions differ and both capability statements list the resource"
        elif ch.category in ("search_param", "resource"):
            conf, why = "HIGH", "v1 capability/resource list has it and v2 does not"
        else:
            conf, why = "LOW", "resource not listed by both capability statements"
        sev, why_sev = _severity(label, ch, v2)
        f = Finding(f"F-{n:03d}", label, conf, conf == "LOW", ch.id, ch.kind, ch.category, ch.resource,
                    ch.v1_path, ch.v2_path, ch.detail, ch.v1_def, ch.v2_def, [_loc(m) for m in ms], why,
                    severity=sev, why_severity=why_sev, sub_kinds=list(ch.sub_kinds),
                    children=list(ch.children), children_count=len(ch.children))
        f.plain_english = _english(f)
        findings.append(f)
        audit.log(cfg.audit_file, "finding", item=f.id, label=label, severity=sev, confidence=conf,
                  element=ch.v1_path or ch.v2_path)

    # A6: things no spec can prove
    for u in find_unverifiable(blocks):
        n += 1
        f = Finding(f"F-{n:03d}", UNVERIFIABLE, "LOW", True, "", UNVERIFIABLE, "statement", "", u.subject, "",
                    f"{u.kind}: no specification can confirm this", "", "",
                    [{"file": u.file, "line": u.line, "section": u.section, "kind": "prose", "token": u.subject,
                      "block_id": u.block_id, "ambiguous": False, "text": u.sentence, "evidence": u.kind}],
                    "headers and policies are not in any machine-readable definition",
                    severity=MEDIUM if u.kind == "header" else LOW, why_severity="a human must verify this")
        f.plain_english = (f"The booklet says (at {u.file}:{u.line}): \"{u.sentence[:140]}\". "
                           f"No specification can prove this {u.kind} statement, so a human should check it.")
        findings.append(f)
        audit.log(cfg.audit_file, "finding", item=f.id, label=UNVERIFIABLE, severity=f.severity, element=u.subject)
    return Analysis(changes, blocks, mentions, findings, v1, v2)


RENAMED_KIND = "RENAMED"


def _english(f: Finding) -> str:
    where = f"{f.locations[0]['file']}:{f.locations[0]['line']}" if f.locations else "nowhere"
    old, new = f.v1_element, f.v2_element
    if f.label == WRONG and f.change_kind in RENAME_KINDS:
        sure = "confirmed by HL7's official map" if f.change_kind == RENAMED_KIND else "a guess; a human should confirm"
        return f"The old booklet talks about `{old}` ({where}). In v2 it is now `{new}` ({sure})."
    if f.label == WRONG:
        return f"The old booklet describes `{old}` ({where}), but in v2 it changed: {f.detail}."
    if f.label == GHOST:
        return f"The old booklet describes `{old}` ({where}), which does not exist in v2 ({f.detail})."
    if f.label == EXAMPLE:
        return f"A sample in the old booklet ({where}) shows `{old}`, which v2 changed or removed ({f.detail})."
    kids = f" It brings {f.children_count} child element(s)." if f.children_count else ""
    return f"v2 {('adds' if f.change_kind == ADDED else 'changes')} `{new or old}` ({f.detail}), and the booklet never mentions it.{kids}"


def fix_first(findings: list[Finding], limit: int = 15) -> list[Finding]:
    pool = [f for f in findings if f.severity in (CRITICAL, HIGH) and f.label != UNVERIFIABLE]
    pool.sort(key=lambda f: (SEVERITY_RANK[f.severity], f.confidence != "HIGH", f.id))
    return pool[:limit]


def write_reports(a: Analysis, cfg: Config, style_findings: list | None = None) -> tuple[Path, Path]:
    cfg.reports_dir.mkdir(parents=True, exist_ok=True)
    by_label: dict[str, list[Finding]] = defaultdict(list)
    by_sev: dict[str, int] = defaultdict(int)
    conf: dict[str, int] = defaultdict(int)
    for f in a.findings:
        by_label[f.label].append(f)
        by_sev[f.severity] += 1
        conf[f.confidence] += 1
    first = fix_first(a.findings)
    summary = {"findings": len(a.findings), "by_label": {k: len(v) for k, v in by_label.items()},
               "by_severity": dict(by_sev), "by_confidence": dict(conf), "spec_changes": len(a.changes),
               "blocks_scanned": len(a.blocks), "mentions_found": len(a.mentions),
               "style_findings": len(style_findings or []), "fix_first": [f.id for f in first]}
    data = {"summary": summary, "spec_changes": [c.to_dict() for c in a.changes],
            "findings": [f.to_dict() for f in a.findings], "style_findings": style_findings or []}
    jp = cfg.reports_dir / "drift-report.json"
    jp.write_text(json.dumps(data, indent=1))
    L = by_label
    md = ["# Drift report", "", "## In plain English", "",
          f"We compared the old v1 booklet with the v1 and v2 API definitions. We found **{summary['findings']} places "
          f"where the booklet may be out of date or unprovable**: {by_sev.get(CRITICAL, 0)} critical, {by_sev.get(HIGH, 0)} high, "
          f"{by_sev.get(MEDIUM, 0)} medium, {by_sev.get(LOW, 0)} low. "
          f"{conf.get('HIGH', 0)} are high confidence; {conf.get('LOW', 0)} are marked \"ask a human\".", "",
          f"By label: {len(L.get(WRONG, []))} wrong, {len(L.get(GHOST, []))} ghost, {len(L.get(EXAMPLE, []))} example, "
          f"{len(L.get(MISSING, []))} missing, {len(L.get(UNVERIFIABLE, []))} unverifiable.", "",
          "- **WRONG**: the text names something that still exists but changed (or was renamed).",
          "- **GHOST**: the text describes something that is gone in v2.",
          "- **EXAMPLE**: only a sample/code block shows the old name.",
          "- **MISSING**: v2 adds or changes it and the booklet is silent.",
          "- **UNVERIFIABLE**: a header or policy statement no specification can prove.", "",
          f"Scanned {summary['blocks_scanned']} pieces of the booklet, found {summary['mentions_found']} element mentions, "
          f"and compared {summary['spec_changes']} differences between the v1 and v2 definitions. "
          f"Style check: {summary['style_findings']} findings (see JSON).", "",
          f"## Fix these first ({len(first)} of {sum(1 for f in a.findings if f.severity in (CRITICAL, HIGH) and f.label != UNVERIFIABLE)} critical/high)", ""]
    if not first:
        md += ["Nothing critical or high.", ""]
    for f in first:
        w = f"{f.locations[0]['file']}:{f.locations[0]['line']}" if f.locations else "-"
        md.append(f"1. **{f.severity}** · {f.label} · {f.confidence}{' (ask a human)' if f.ask_human else ''} · "
                  f"`{f.v1_element or f.v2_element}` · {w}  \n   {f.plain_english}")
    md.append("")
    for label in (WRONG, GHOST, EXAMPLE):
        fs = [f for f in L.get(label, []) if f.severity != LOW]
        md += [f"## {label} ({len(fs)})", ""]
        if not fs:
            md += ["None.", ""]
            continue
        md += ["| ID | Severity | Confidence | Element (v1 → v2) | Where | What |", "|---|---|---|---|---|---|"]
        for f in sorted(fs, key=lambda x: (SEVERITY_RANK[x.severity], x.id)):
            w = f"{f.locations[0]['file']}:{f.locations[0]['line']}" if f.locations else "-"
            md.append(f"| {f.id} | {f.severity} | {f.confidence}{' (ask a human)' if f.ask_human else ''} | "
                      f"`{f.v1_element or '-'}` → `{f.v2_element or '-'}` | {w} | {f.detail} |")
        md.append("")
    miss = [f for f in L.get(MISSING, []) if f.severity != LOW]
    md += [f"## MISSING, medium ({len(miss)})", ""]
    for f in miss:
        kids = f" (+{f.children_count} child elements: {', '.join(c.split('.')[-1] for c in f.children[:8])}{'…' if f.children_count > 8 else ''})" if f.children_count else ""
        md.append(f"- {f.id} `{f.v2_element or f.v1_element}`: {f.detail}{kids}")
    md.append("")
    unv = L.get(UNVERIFIABLE, [])
    md += [f"## UNVERIFIABLE: a human must check ({len(unv)})", "",
           "Headers and policies are not in any specification. Each needs a person to confirm it.", ""]
    for f in unv:
        loc = f.locations[0]
        md.append(f"- **{f.v1_element}** ({loc['file']}:{loc['line']}, {f.severity}): {loc['text'][:160]}")
    md += ["", "## Appendix: LOW items by resource", ""]
    low = [f for f in a.findings if f.severity == LOW and f.label != UNVERIFIABLE]
    for res in sorted({f.resource or "(other)" for f in low}):
        items = [f for f in low if (f.resource or "(other)") == res]
        md += [f"### {res} ({len(items)})", ""]
        for f in items:
            kids = f" (+{f.children_count} children)" if f.children_count else ""
            md.append(f"- {f.id} {f.label} `{f.v2_element or f.v1_element}`: {f.detail}{kids}")
        md.append("")
    mp = cfg.reports_dir / "drift-report.md"
    mp.write_text("\n".join(md) + "\n")
    audit.log(cfg.audit_file, "report_written", item=str(mp))
    return mp, jp

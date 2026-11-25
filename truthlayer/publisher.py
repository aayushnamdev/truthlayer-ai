"""2D. Publish: one Markdown page per doc section, llms.txt, llms-full.txt and a Word export.
Only APPROVED fixes are applied. Pages still carrying open findings say so."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from . import __version__, audit, sample_edit
from .config import Config
from .drift import Analysis


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "page"


def _sections(lines: list[str]) -> list[tuple[str, int, int]]:
    """Split a file at H1/H2 headings. Returns (title, first_line, last_line), 1-based."""
    starts = [(i + 1, re.sub(r"^#+\s*", "", l).strip()) for i, l in enumerate(lines)
              if re.match(r"^#{1,2}\s+\S", l)]
    out = []
    if not starts or starts[0][0] > 1:
        end = (starts[0][0] - 1) if starts else len(lines)
        if any(l.strip() for l in lines[:end]):
            out.append(("Introduction", 1, end))
    for k, (ln, title) in enumerate(starts):
        end = starts[k + 1][0] - 1 if k + 1 < len(starts) else len(lines)
        out.append((title, ln, end))
    return out


def _apply_fix(seg: list[str], p: dict) -> tuple[list[str], bool]:
    """Apply one approved fix to the lines of its block. Uses the small old/new edit when there is one
    (so code fences and surrounding text are never touched); otherwise replaces the block with the proposed text."""
    text = "\n".join(seg)
    e = p.get("edit") or sample_edit.edit_from_rewrite(p.get("original", ""), p.get("proposed", ""))
    if e and e.get("old_text") and text.count(e["old_text"]) == 1:
        return text.replace(e["old_text"], e["new_text"], 1).split("\n"), True
    if p.get("kind") in ("sample", "code"):
        return seg, False            # never replace a whole code block with a rewrite
    return p["proposed"].split("\n"), True


def _apply_section(sec_lines: list[str], lo: int, fixes: list[dict]) -> tuple[list[str], list[dict]]:
    lines = list(sec_lines)
    applied: list[dict] = []
    for p in sorted(fixes, key=lambda p: -p["line"]):
        a, b = p["line"] - lo, p["end_line"] - lo + 1
        new, ok = _apply_fix(lines[a:b], p)
        if ok:
            lines[a:b] = new
            applied.append(p)
    return lines, applied


def _publish_samples(cfg: Config, approved: list[dict], out: Path) -> list[dict]:
    """Corrected copies of the JSON sample files (only approved fixes; every result is re-checked as valid JSON)."""
    import json as _json
    sdir = out / "samples"
    sdir.mkdir(parents=True, exist_ok=True)
    for old in sdir.glob("*.json"):
        old.unlink()
    by_file: dict[str, list[dict]] = {}
    for p in approved:
        if p["file"].endswith(".json"):
            by_file.setdefault(p["file"], []).append(p)
    res: list[dict] = []
    for file, fixes in sorted(by_file.items()):
        src = cfg.root / file
        if not src.exists():
            continue
        lines = src.read_text(encoding="utf-8").split("\n")
        applied = 0
        for p in sorted(fixes, key=lambda p: -p["line"]):
            a, b = p["line"] - 1, p["end_line"]
            new, ok = _apply_fix(lines[a:b], p)
            if ok:
                lines[a:b] = new
                applied += 1
        text = "\n".join(lines)
        try:
            _json.loads(text)
        except _json.JSONDecodeError as exc:
            audit.log(cfg.audit_file, "publish_sample_rejected", item=file, reason=exc.msg)
            continue
        if applied:
            name = Path(file).name
            (sdir / name).write_text(text, encoding="utf-8")
            res.append({"file": file, "published_as": f"samples/{name}", "fixes_applied": applied,
                        "sha256": audit.sha256_text(text), "valid_json": True})
            audit.log(cfg.audit_file, "publish_sample", item=name, fixes=applied)
    return res


def publish(a: Analysis, cfg: Config, proposals: dict | None = None) -> dict:
    out = cfg.publish_dir
    (out / "pages").mkdir(parents=True, exist_ok=True)
    for old in (out / "pages").glob("*.md"):
        old.unlink()
    props = (proposals or {"proposals": []})["proposals"]
    approved = [p for p in props if p["status"] == "APPROVED" and p["file"].endswith((".md", ".json")) and p["changed"]]
    today = date.today().isoformat()
    v_hashes = {str(f.name): audit.sha256_file(f) for f in cfg.defs_v1 + cfg.defs_v2}
    manifest: dict[str, Any] = {"truthlayer_version": __version__, "published_on": today, "pages": []}
    skipped = [p["id"] for p in props if p["status"] == "APPROVED" and not p["file"].endswith((".md", ".json"))]
    if (out / "samples").exists():
        for old in (out / "samples").glob("*.json"):
            old.unlink()
    docs = sorted(Path(cfg.docs_dir).glob("*.md"))
    for f in docs:
        disp = str(f.relative_to(cfg.root)) if f.is_relative_to(cfg.root) else str(f)
        raw = f.read_text(encoding="utf-8")
        lines = raw.split("\n")
        src_hash = audit.sha256_file(f)
        fixes = [p for p in approved if p["file"] == disp]
        for title, lo, hi in _sections(lines):
            sec_fixes = [p for p in fixes if lo <= p["line"] and p["end_line"] <= hi]
            sec, applied_fixes = _apply_section(lines[lo - 1:hi], lo, sec_fixes)
            sec_fixes = applied_fixes
            fixed_ids = {p["finding_id"] for p in sec_fixes}
            open_f = [x for x in a.findings if x.label != "MISSING" and x.id not in fixed_ids
                      and any(l["file"] == disp and lo <= l["line"] <= hi for l in x.locations)]
            pid = f"{f.stem}--{slug(title)}"
            body = "\n".join(sec).strip() + "\n"
            fm = ["---", f'id: "{pid}"', f'title: "{title}"', 'api_version: "2 (FHIR R4)"',
                  f"verified_on: {today}", "source:", f'  file: "{disp}"', f'  sha256: "{src_hash}"',
                  f'  lines: "{lo}-{hi}"', "spec_hashes:"]
            fm += [f'  {k}: "{v}"' for k, v in sorted(v_hashes.items())]
            fm += [f'truthlayer_version: "{__version__}"', f"fixes_applied: {len(sec_fixes)}",
                   f"open_findings: {len(open_f)}",
                   f'status: "{"verified" if not open_f else "needs_review"}"', "---", ""]
            banner = ""
            if open_f:
                banner = (f"> **Not fully verified:** {len(open_f)} finding(s) on this section are still open "
                          f"({', '.join(sorted({x.id for x in open_f}))}). See reports/drift-report.md.\n\n")
            (out / "pages" / f"{pid}.md").write_text("\n".join(fm) + banner + body, encoding="utf-8")
            manifest["pages"].append({"id": pid, "title": title, "file": disp, "lines": [lo, hi],
                                      "fixes_applied": len(sec_fixes), "open_findings": len(open_f),
                                      "api_version": "2 (FHIR R4)", "verified_on": today,
                                      "sha256": audit.sha256_text(body)})
            audit.log(cfg.audit_file, "publish", item=pid, fixes=len(sec_fixes), open_findings=len(open_f))
    manifest["samples"] = _publish_samples(cfg, approved, out)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    _llms(out, manifest)
    _docx(out, manifest, cfg)
    manifest["skipped_unpublishable_approved"] = skipped
    return manifest


def _strip_fm(text: str) -> str:
    return re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.S)


def _llms(out: Path, manifest: dict):
    head = ["# TruthLayer verified docs: Blue Button API (v1 booklet checked against v2 / FHIR R4)", "",
            "> Pages are the old booklet, checked against the FHIR R4 definitions. Pages marked "
            "needs_review still have open findings. Only human-approved (or auto-approved HIGH-confidence) fixes are applied.", "",
            "## Pages", ""]
    for p in manifest["pages"]:
        head.append(f"- [{p['title']}](pages/{p['id']}.md): {p['file']} lines {p['lines'][0]}-{p['lines'][1]}; "
                    f"{p['fixes_applied']} fixes, {p['open_findings']} open findings")
    if manifest.get("samples"):
        head += ["", "## Corrected samples", ""]
        head += [f"- [{x['published_as']}]({x['published_as']}): from {x['file']}; {x['fixes_applied']} approved fix(es), valid JSON"
                 for x in manifest["samples"]]
    (out / "llms.txt").write_text("\n".join(head) + "\n", encoding="utf-8")
    full = ["# TruthLayer verified docs (full text)", ""]
    for p in manifest["pages"]:
        text = (out / "pages" / f"{p['id']}.md").read_text(encoding="utf-8")
        full += [f"<!-- page: {p['id']} -->", _strip_fm(text), ""]
    (out / "llms-full.txt").write_text("\n".join(full), encoding="utf-8")


def _docx(out: Path, manifest: dict, cfg: Config):
    from docx import Document
    from docx.shared import Pt
    d = Document()
    d.add_heading("Blue Button API documentation", 0)
    d.add_paragraph("Old v1 booklet, checked against v2 (FHIR R4) by TruthLayer AI")
    d.add_paragraph(f"Verified on {manifest['published_on']} - TruthLayer {manifest['truthlayer_version']}")
    d.add_page_break()
    d.add_heading("Versions and sources", 1)
    t = d.add_table(rows=1, cols=4)
    t.style = "Table Grid"
    for c, h in zip(t.rows[0].cells, ["Page", "API version", "Fixes applied", "Open findings"]):
        c.text = h
    for p in manifest["pages"]:
        r = t.add_row().cells
        r[0].text, r[1].text, r[2].text, r[3].text = p["title"], p["api_version"], str(p["fixes_applied"]), str(p["open_findings"])
    d.add_page_break()
    for p in manifest["pages"]:
        body = _strip_fm((out / "pages" / f"{p['id']}.md").read_text(encoding="utf-8"))
        incode = False
        for l in body.split("\n"):
            if l.strip().startswith("```"):
                incode = not incode
                continue
            if incode:
                run = d.add_paragraph().add_run(l)
                run.font.name = "Courier New"; run.font.size = Pt(8)
            elif re.match(r"^#{1,6}\s", l):
                d.add_heading(re.sub(r"^#+\s*", "", l), min(len(l) - len(l.lstrip("#")), 3))
            elif l.strip():
                d.add_paragraph(re.sub(r"<[^>]+>", "", l))
    d.save(str(out / "export.docx"))

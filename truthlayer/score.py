"""Phase 5 scoring: compare findings with CMS's own v1->v2 change list. Only used at the scoring step."""
from __future__ import annotations
import csv, json, re
from pathlib import Path


def _norm_items(s: str) -> list[str]:
    out = []
    for part in s.split(";"):
        part = re.sub(r"\(.*?\)", "", part)
        part = re.sub(r"\s+value set.*$", "", part, flags=re.I).strip()
        if not part or part.lower().startswith("http header") or "." not in part:
            continue
        head, rest = part.split(".", 1)
        if head.lower() == "eob":
            head = "ExplanationOfBenefit"
        out.append(f"{head}.{rest}".lower().replace("[x]", ""))
    return out


def _match(key: str, path: str) -> bool:
    p = path.lower().replace("[x]", "")
    if not p:
        return False
    if p == key or p.startswith(key + "."):
        return True
    kr, kl = key.split(".")[0], key.split(".")[-1]
    return p.split(".")[0] == kr and p.split(".")[-1] == kl


def score(csv_path: Path, report_json: Path) -> dict:
    rep = json.loads(Path(report_json).read_text())
    rows = list(csv.DictReader(open(csv_path, newline="", encoding="utf-8")))
    findings, changes = rep["findings"], rep["spec_changes"]
    result_rows = []
    matched_findings: set[str] = set()
    for r in rows:
        keys_v1, keys_v2 = _norm_items(r["v1_element"]), _norm_items(r["v2_element"])
        keys = [(k, "v1") for k in keys_v1] + [(k, "v2") for k in keys_v2]
        fh = []
        for f in findings:
            if any(_match(k, f["v1_element"]) or _match(k, f["v2_element"]) for k, _ in keys):
                fh.append(f)
        ch = [c for c in changes if any(_match(k, c["v1_path"]) or _match(k, c["v2_path"]) for k, _ in keys)]
        for f in fh:
            matched_findings.add(f["id"])
        status = "caught" if fh else ("in-spec-diff-only" if ch else "missed")
        result_rows.append({"change_id": r["change_id"], "resource": r["resource"], "change_type": r["change_type"],
                            "v1_element": r["v1_element"], "v2_element": r["v2_element"], "status": status,
                            "labels": sorted({f["label"] for f in fh}),
                            "finding_ids": [f["id"] for f in fh], "spec_change_kinds": sorted({c["kind"] for c in ch})})
    n = len(rows)
    caught = sum(1 for x in result_rows if x["status"] == "caught")
    diffonly = sum(1 for x in result_rows if x["status"] == "in-spec-diff-only")
    unmatched = [f for f in findings if f["id"] not in matched_findings]
    return {"rows": result_rows, "n": n, "caught": caught, "spec_diff_only": diffonly,
            "missed": n - caught - diffonly, "recall_findings": caught / n if n else 0,
            "recall_spec_diff": (caught + diffonly) / n if n else 0,
            "findings_total": len(findings), "findings_matched": len(findings) - len(unmatched),
            "precision": (len(findings) - len(unmatched)) / len(findings) if findings else 0,
            "unmatched_findings": unmatched}

"""1B. Compare v1 and v2 definitions. Plain deterministic code."""
from __future__ import annotations
import difflib, re
from dataclasses import dataclass, field, asdict
from .fhir_adapter import Element, Capability

ADDED, REMOVED, CHANGED, POSSIBLE_RENAME = "ADDED", "REMOVED", "CHANGED", "POSSIBLE_RENAME"


@dataclass
class SpecChange:
    id: str
    kind: str                 # ADDED | REMOVED | CHANGED | POSSIBLE_RENAME
    category: str             # element | search_param | resource | interaction
    resource: str
    v1_path: str = ""
    v2_path: str = ""
    detail: str = ""
    v1_def: str = ""
    v2_def: str = ""
    needs_human_check: bool = False
    rename_score: float = 0.0
    collapsed_descendants: int = 0

    def to_dict(self):
        return asdict(self)


def _tokens(name: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", name.replace("[x]", ""))}


def _base(name: str) -> str:
    return name.replace("[x]", "")


def rename_score(old: Element, new: Element) -> float:
    a, b = _base(old.name).lower(), _base(new.name).lower()
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    ta, tb = _tokens(old.name), _tokens(new.name)
    jac = len(ta & tb) / len(ta | tb) if ta | tb else 0.0
    score = max(ratio, jac)
    first_a = re.match(r"[a-z]+", _base(old.name))
    first_b = re.match(r"[a-z]+", _base(new.name))
    if first_a and first_b and first_a.group() == first_b.group() and len(first_a.group()) >= 4:
        score = max(score, 0.5)
    if old.types and old.types == new.types:
        score += 0.1
    return round(min(score, 1.0), 3)


def _parent(path: str) -> str:
    return path.rsplit(".", 1)[0] if "." in path else ""


def diff_elements(v1: dict[str, Element], v2: dict[str, Element]) -> list[SpecChange]:
    out: list[SpecChange] = []
    n = 0

    def nid():
        nonlocal n
        n += 1
        return f"SC-{n:03d}"

    removed = sorted(p for p in v1 if p not in v2)
    added = sorted(p for p in v2 if p not in v1)
    # collapse subtrees: only report the topmost removed/added element
    top_removed = [p for p in removed if _parent(p) not in set(removed)]
    top_added = [p for p in added if _parent(p) not in set(added)]
    desc_r = {p: sum(1 for q in removed if q.startswith(p + ".")) for p in top_removed}
    desc_a = {p: sum(1 for q in added if q.startswith(p + ".")) for p in top_added}

    # rename candidates: same parent, similar names. Always "needs human check".
    pairs: list[tuple[float, str, str]] = []
    for r in top_removed:
        for a in top_added:
            if _parent(r) == _parent(a):
                s = rename_score(v1[r], v2[a])
                if s >= 0.55:
                    pairs.append((s, r, a))
    pairs.sort(reverse=True)
    used_r, used_a = set(), set()
    for s, r, a in pairs:
        if r in used_r or a in used_a:
            continue
        used_r.add(r); used_a.add(a)
        out.append(SpecChange(nid(), POSSIBLE_RENAME, "element", v1[r].resource, r, a,
                              f"{v1[r].name} may have become {v2[a].name} (similarity {s})",
                              v1[r].describe(), v2[a].describe(), True, s,
                              desc_r.get(r, 0)))
    for r in top_removed:
        if r not in used_r:
            out.append(SpecChange(nid(), REMOVED, "element", v1[r].resource, r, "", "not in v2",
                                  v1[r].describe(), "", False, 0.0, desc_r.get(r, 0)))
    for a in top_added:
        if a not in used_a:
            out.append(SpecChange(nid(), ADDED, "element", v2[a].resource, "", a, "new in v2",
                                  "", v2[a].describe(), False, 0.0, desc_a.get(a, 0)))
    for p in sorted(set(v1) & set(v2)):
        e1, e2 = v1[p], v2[p]
        why = []
        if e1.types != e2.types:
            why.append(f"type {'|'.join(e1.types) or 'Backbone'} -> {'|'.join(e2.types) or 'Backbone'}")
        if (e1.min, e1.max) != (e2.min, e2.max):
            why.append(f"cardinality {e1.card} -> {e2.card}")
        if why:
            out.append(SpecChange(nid(), CHANGED, "element", e1.resource, p, p, "; ".join(why),
                                  e1.describe(), e2.describe()))
    return out


def diff_capability(c1: Capability, c2: Capability, start: int = 0) -> list[SpecChange]:
    out: list[SpecChange] = []
    n = start

    def nid():
        nonlocal n
        n += 1
        return f"SC-{n:03d}"

    for r in sorted(set(c1.resources) | set(c2.resources)):
        a, b = c1.resources.get(r), c2.resources.get(r)
        if a and not b:
            out.append(SpecChange(nid(), REMOVED, "resource", r, r, "", "resource not in v2 capability statement"))
            continue
        if b and not a:
            out.append(SpecChange(nid(), ADDED, "resource", r, "", r, "resource new in v2 capability statement"))
            continue
        for s in sorted(a["search"] - b["search"]):
            out.append(SpecChange(nid(), REMOVED, "search_param", r, f"{r}?{s}", "", "search parameter not in v2"))
        for s in sorted(b["search"] - a["search"]):
            out.append(SpecChange(nid(), ADDED, "search_param", r, "", f"{r}?{s}", "search parameter new in v2"))
        for i in sorted(a["interactions"] - b["interactions"]):
            out.append(SpecChange(nid(), REMOVED, "interaction", r, f"{r}:{i}", "", "interaction not in v2"))
        for i in sorted(b["interactions"] - a["interactions"]):
            out.append(SpecChange(nid(), ADDED, "interaction", r, "", f"{r}:{i}", "interaction new in v2"))
    return out


def run_diff(v1, v2, c1: Capability, c2: Capability) -> list[SpecChange]:
    el = diff_elements(v1, v2)
    return el + diff_capability(c1, c2, start=len(el))

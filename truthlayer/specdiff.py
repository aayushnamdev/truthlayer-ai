"""1B. Compare v1 and v2 definitions. Plain deterministic code."""
from __future__ import annotations
import difflib, re
from dataclasses import dataclass, field, asdict
from .fhir_adapter import Element, Capability

ADDED, REMOVED, CHANGED, POSSIBLE_RENAME = "ADDED", "REMOVED", "CHANGED", "POSSIBLE_RENAME"
RENAMED = "RENAMED"          # confirmed by HL7's official R3 -> R4 map
RENAME_KINDS = (RENAMED, POSSIBLE_RENAME)


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
    sub_kinds: list[str] = field(default_factory=list)   # type, cardinality, now_required, value_set, ...
    children: list[str] = field(default_factory=list)    # elements folded under a new/removed parent
    rename_source: str = ""                              # "HL7 R3-R4 map" or "name similarity"

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


def _vs_base(vs: str) -> str:
    return vs.split("|")[0]


def rule_diffs(e1: Element, e2: Element) -> tuple[list[str], list[str]]:
    """(sub_kinds, human-readable reasons) for everything that differs between two elements."""
    kinds: list[str] = []
    why: list[str] = []
    if e1.types != e2.types:
        kinds.append("type")
        why.append(f"type {'|'.join(e1.types) or 'Backbone'} -> {'|'.join(e2.types) or 'Backbone'}")
    if (e1.min, e1.max) != (e2.min, e2.max):
        kinds.append("cardinality")
        why.append(f"cardinality {e1.card} -> {e2.card}")
        if e1.min == 0 and e2.min >= 1:
            kinds.append("now_required")
    if e1.binding != e2.binding:
        if _vs_base(e1.binding) != _vs_base(e2.binding):
            kinds.append("value_set")
            why.append(f"value set {e1.binding or '(none)'} -> {e2.binding or '(none)'}")
        else:
            kinds.append("value_set_version")
            why.append(f"value set version {e1.binding} -> {e2.binding}")
    if e1.strength != e2.strength and (e1.strength or e2.strength) and (e1.binding or e2.binding):
        kinds.append("binding_strength")
        why.append(f"binding strength {e1.strength or '(none)'} -> {e2.strength or '(none)'}")
    if e1.fixed != e2.fixed:
        kinds.append("fixed_default")
        why.append(f"fixed/default value {e1.fixed or '(none)'} -> {e2.fixed or '(none)'}")
    if e1.targets != e2.targets:
        kinds.append("target_type")
        why.append(f"reference targets {'|'.join(e1.targets) or '(any)'} -> {'|'.join(e2.targets) or '(any)'}")
    if e1.must_support != e2.must_support:
        kinds.append("must_support")
        why.append(f"must-support {e1.must_support} -> {e2.must_support}")
    if e1.slicing != e2.slicing:
        kinds.append("slicing")
        why.append(f"slicing '{e1.slicing or 'none'}' -> '{e2.slicing or 'none'}'")
    return kinds, why


def diff_elements(v1: dict[str, Element], v2: dict[str, Element],
                  official_renames: dict[str, str] | None = None) -> list[SpecChange]:
    out: list[SpecChange] = []
    n = 0
    official_renames = {k: v for k, v in (official_renames or {}).items() if ".extension" not in v}

    def nid():
        nonlocal n
        n += 1
        return f"SC-{n:03d}"

    removed = sorted(p for p in v1 if p not in v2)
    added = sorted(p for p in v2 if p not in v1)
    removed_set, added_set = set(removed), set(added)
    top_removed = [p for p in removed if _parent(p) not in removed_set]
    top_added = [p for p in added if _parent(p) not in added_set]
    kids_r = {p: [q for q in removed if q.startswith(p + ".")] for p in top_removed}
    kids_a = {p: [q for q in added if q.startswith(p + ".")] for p in top_added}
    used_r: set[str] = set()
    used_a: set[str] = set()

    # 1. official HL7 R3 -> R4 renames (also when the parent changed)
    for r, a in sorted(official_renames.items()):
        if r in removed_set and a in added_set and r not in used_r and a not in used_a:
            used_r.add(r); used_a.add(a)
            out.append(SpecChange(nid(), RENAMED, "element", v1[r].resource, r, a,
                                  f"{v1[r].name} was renamed {v2[a].name} (HL7 R3-R4 map)",
                                  v1[r].describe(), v2[a].describe(), False, 1.0,
                                  len(kids_r.get(r, [])), ["renamed"], kids_r.get(r, []), "HL7 R3-R4 map"))
    # 2. fall back to name similarity; always needs a human
    pairs: list[tuple[float, str, str]] = []
    for r in top_removed:
        for a in top_added:
            if r in used_r or a in used_a or _parent(r) != _parent(a):
                continue
            sc = rename_score(v1[r], v2[a])
            if sc >= 0.55:
                pairs.append((sc, r, a))
    pairs.sort(reverse=True)
    for sc, r, a in pairs:
        if r in used_r or a in used_a:
            continue
        used_r.add(r); used_a.add(a)
        out.append(SpecChange(nid(), POSSIBLE_RENAME, "element", v1[r].resource, r, a,
                              f"{v1[r].name} may have become {v2[a].name} (similarity {sc})",
                              v1[r].describe(), v2[a].describe(), True, sc, len(kids_r.get(r, [])),
                              ["renamed"], kids_r.get(r, []), "name similarity"))
    for r in top_removed:
        if r not in used_r:
            out.append(SpecChange(nid(), REMOVED, "element", v1[r].resource, r, "", "not in v2",
                                  v1[r].describe(), "", False, 0.0, len(kids_r[r]), ["removed"], kids_r[r]))
    for a in top_added:
        if a not in used_a:
            out.append(SpecChange(nid(), ADDED, "element", v2[a].resource, "", a, "new in v2",
                                  "", v2[a].describe(), False, 0.0, len(kids_a[a]), ["added"], kids_a[a]))
    for p in sorted(set(v1) & set(v2)):
        kinds, why = rule_diffs(v1[p], v2[p])
        if kinds:
            out.append(SpecChange(nid(), CHANGED, "element", v1[p].resource, p, p, "; ".join(why),
                                  v1[p].describe(), v2[p].describe(), sub_kinds=kinds))
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


def run_diff(v1, v2, c1: Capability, c2: Capability,
             official_renames: dict[str, str] | None = None) -> list[SpecChange]:
    el = diff_elements(v1, v2, official_renames)
    return el + diff_capability(c1, c2, start=len(el))

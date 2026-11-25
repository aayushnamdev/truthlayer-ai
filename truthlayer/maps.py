"""Parse HL7's official FHIR R3 -> R4 version maps (FHIR Mapping Language shown on the
`<resource>-version-maps.html` pages) into {R3 path: R4 path} for elements that were renamed."""
from __future__ import annotations
import html
import re
from pathlib import Path

GROUP = re.compile(r"^group (\w+)\(source src(?: : (\w+))?, target tgt(?: : (\w+))?\)")
RULE = re.compile(r"src\.(\w+)(?: as (\w+))? -> tgt\.(\w+)(?: as (\w+))?(?: then (\w+)\((\w+), (\w+)\))?;")


def parse_version_map(path: Path) -> dict[str, str]:
    text = html.unescape(re.sub(r"<[^>]+>", "", Path(path).read_text(encoding="utf-8")))
    groups: dict[str, list[tuple[str, str, str]]] = {}
    root = ""
    current: list[tuple[str, str, str]] | None = None
    for line in text.split("\n"):
        g = GROUP.match(line.strip())
        if g:
            if g.group(1) in groups:       # the page repeats its groups for the R4 -> R3 map: stop
                break
            current = groups.setdefault(g.group(1), [])
            if g.group(3) and not root:
                root = g.group(1)
            continue
        m = RULE.search(line)
        if m and current is not None:
            current.append((m.group(1), m.group(3), m.group(5) or ""))
    out: dict[str, str] = {}

    def walk(group: str, src: str, tgt: str, depth: int = 0) -> None:
        if depth > 8:
            return
        for s_name, t_name, sub in groups.get(group, []):
            sp, tp = f"{src}.{s_name}", f"{tgt}.{t_name}"
            if s_name != t_name:
                out[sp] = tp
            if sub:
                walk(sub, sp, tp, depth + 1)

    if root:
        walk(root, root, root)
    return out

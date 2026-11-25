"""1A. Read StructureDefinitions + capability statements into plain dictionaries."""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path

# Generic FHIR plumbing that every resource has; not interesting for drift.
SKIP_SUFFIXES = (".id", ".meta", ".implicitRules", ".language", ".text", ".contained",
                 ".extension", ".modifierExtension")


@dataclass(frozen=True)
class Element:
    path: str
    types: tuple[str, ...]
    min: int
    max: str  # "1", "*" ...
    short: str = ""

    @property
    def card(self) -> str:
        return f"{self.min}..{self.max}"

    @property
    def name(self) -> str:
        return self.path.rsplit(".", 1)[-1]

    @property
    def resource(self) -> str:
        return self.path.split(".", 1)[0]

    def describe(self) -> str:
        return f"{self.path} [{self.card}] type={'|'.join(self.types) or 'BackboneElement'}"


def load_definitions(files: list[Path]) -> dict[str, Element]:
    """path -> Element, across all files. `[x]` choice paths are kept as written."""
    out: dict[str, Element] = {}
    for f in files:
        sd = json.loads(Path(f).read_text(encoding="utf-8"))
        for e in sd.get("snapshot", {}).get("element", []):
            path = e["path"]
            if "." not in path or path.endswith(SKIP_SUFFIXES) or ".extension" in path:
                continue
            types = tuple(sorted({t.get("code", "") for t in e.get("type", [])}))
            out[path] = Element(path=path, types=types, min=int(e.get("min", 0)),
                                max=str(e.get("max", "1")), short=e.get("short", ""))
    return out


@dataclass
class Capability:
    fhir_version: str = ""
    software: str = ""
    resources: dict[str, dict] = field(default_factory=dict)  # name -> {interactions:set, search:set}


def load_capability(p: Path | None) -> Capability:
    cap = Capability()
    if not p or not Path(p).exists():
        return cap
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    cap.fhir_version = d.get("fhirVersion", "")
    cap.software = (d.get("software") or {}).get("name", "")
    for rest in d.get("rest", []):
        for r in rest.get("resource", []):
            cap.resources[r["type"]] = {
                "interactions": {i["code"] for i in r.get("interaction", [])},
                "search": {s["name"] for s in r.get("searchParam", [])},
            }
    return cap


def load_types(p: Path | None) -> set[str]:
    if not p or not Path(p).exists():
        return set()
    return set(json.loads(Path(p).read_text())["resource_types"])

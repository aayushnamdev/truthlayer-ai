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
    binding: str = ""          # value set URL (version kept)
    strength: str = ""         # required | extensible | preferred | example
    fixed: str = ""            # fixed / pattern / default value, as JSON text
    targets: tuple[str, ...] = ()   # reference target resource types
    must_support: bool = False
    slicing: str = ""          # e.g. "slices by pattern:type; required: memberid"

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
        bits = [f"{self.path} [{self.card}] type={'|'.join(self.types) or 'BackboneElement'}"]
        if self.targets:
            bits.append("refers to " + "|".join(self.targets))
        if self.binding:
            bits.append(f"binding {self.strength or '?'}: {self.binding}")
        if self.fixed:
            bits.append(f"fixed/default {self.fixed}")
        if self.must_support:
            bits.append("must-support")
        if self.slicing:
            bits.append(self.slicing)
        return "; ".join(bits)


def _binding(e: dict) -> tuple[str, str]:
    b = e.get("binding") or {}
    vs = b.get("valueSet") or b.get("valueSetUri") or (b.get("valueSetReference") or {}).get("reference") or ""
    return str(vs), str(b.get("strength", ""))


def _targets(e: dict) -> tuple[str, ...]:
    out: set[str] = set()
    for t in e.get("type", []):
        tp = t.get("targetProfile")
        for x in ([tp] if isinstance(tp, str) else (tp or [])):
            out.add(x.rsplit("/", 1)[-1])
    return tuple(sorted(out))


def _fixed(e: dict) -> str:
    for k, v in e.items():
        if k.startswith(("fixed", "pattern", "defaultValue")):
            return f"{k}={json.dumps(v, sort_keys=True)}"
    return ""


def _read_sd(f: Path) -> dict:
    try:
        sd = json.loads(Path(f).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(f"definition file not found: {f}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"{f} is not valid JSON ({exc.msg} at line {exc.lineno})") from None
    if not isinstance(sd, dict) or sd.get("resourceType") != "StructureDefinition":
        raise ValueError(f"{f} is not a FHIR StructureDefinition")
    if "snapshot" not in sd:
        raise ValueError(f"{f} has no snapshot; use the snapshot form of the StructureDefinition")
    return sd


def _plain(e: dict) -> bool:
    path = e["path"]
    return "." in path and not path.endswith(SKIP_SUFFIXES) and ".extension" not in path and ":" not in e.get("id", "")


def _to_element(e: dict) -> Element:
    vs, st = _binding(e)
    types = tuple(sorted({t.get("code", "") for t in e.get("type", [])}))
    return Element(path=e["path"], types=types, min=int(e.get("min", 0)), max=str(e.get("max", "1")),
                   short=e.get("short", ""), binding=vs, strength=st, fixed=_fixed(e), targets=_targets(e),
                   must_support=bool(e.get("mustSupport", False)))


def load_definitions(files: list[Path]) -> dict[str, Element]:
    """path -> Element, across all files. `[x]` choice paths are kept as written."""
    out: dict[str, Element] = {}
    for f in files:
        sd = _read_sd(Path(f))
        for e in sd["snapshot"].get("element", []):
            if _plain(e):
                out[e["path"]] = _to_element(e)
    return out


def load_profile_overlay(files: list[Path]) -> dict[str, dict]:
    """Rules a profile (e.g. CARIN BB, CMS Blue Button IG) adds on top of the base resource:
    must-support, slicing, required slices, stricter minimum, binding, fixed values."""
    ov: dict[str, dict] = {}
    for f in files:
        sd = _read_sd(Path(f))
        els = sd["snapshot"].get("element", [])
        for e in els:
            path = e["path"]
            if "." not in path or ".extension" in path or path.endswith(SKIP_SUFFIXES):
                continue
            if ":" in e.get("id", ""):
                # a named slice of some element: remember required ones
                base_id = e["id"].split(":", 1)[0]
                if e["id"].count(":") == 1 and e["id"].endswith(e["id"].split(":", 1)[1]) and "." not in e["id"].split(":", 1)[1]:
                    d = ov.setdefault(base_id, {})
                    d.setdefault("slices", {})[e.get("sliceName", e["id"].split(":", 1)[1])] = int(e.get("min", 0))
                continue
            d = ov.setdefault(path, {})
            d["must_support"] = d.get("must_support", False) or bool(e.get("mustSupport", False))
            d["min"] = max(d.get("min", 0), int(e.get("min", 0)))
            if e.get("slicing") and "slicing" not in d:
                disc = ",".join(f"{x.get('type')}:{x.get('path')}" for x in e["slicing"].get("discriminator", []))
                d["slicing"] = disc or "unspecified"
            vs, st = _binding(e)
            if vs and not d.get("binding"):
                d["binding"], d["strength"] = vs, st
            fx = _fixed(e)
            if fx and not d.get("fixed"):
                d["fixed"] = fx
    return ov


def apply_profiles(base: dict[str, Element], overlay: dict[str, dict]) -> dict[str, Element]:
    out = dict(base)
    for path, d in overlay.items():
        e = out.get(path)
        if e is None:
            continue
        slicing = e.slicing
        if d.get("slicing") or d.get("slices"):
            req = sorted(n for n, m in (d.get("slices") or {}).items() if m >= 1)
            slicing = f"sliced by {d.get('slicing', '?')}" + (f"; required slices: {', '.join(req)}" if req else "")
        out[path] = Element(e.path, e.types, max(e.min, d.get("min", 0)), e.max, e.short,
                            d.get("binding") or e.binding, d.get("strength") or e.strength,
                            d.get("fixed") or e.fixed, e.targets, e.must_support or d.get("must_support", False),
                            slicing)
    return out


@dataclass
class Capability:
    fhir_version: str = ""
    software: str = ""
    resources: dict[str, dict] = field(default_factory=dict)  # name -> {interactions:set, search:set}


def load_capability(p: Path | None) -> Capability:
    cap = Capability()
    if not p:
        return cap
    if not Path(p).exists():
        raise FileNotFoundError(f"capability statement not found: {p}")
    try:
        d = json.loads(Path(p).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{p} is not valid JSON ({exc.msg} at line {exc.lineno})") from None
    if d.get("resourceType") != "CapabilityStatement":
        raise ValueError(f"{p} is not a FHIR CapabilityStatement")
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


def load_maps(files: list[Path]) -> dict[str, str]:
    """Official HL7 R3->R4 renames, {v1 path: v2 path}. Empty if no map files are given."""
    from .maps import parse_version_map
    out: dict[str, str] = {}
    for f in files:
        if Path(f).exists():
            out.update(parse_version_map(Path(f)))
    return out

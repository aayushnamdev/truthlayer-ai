"""Where the inputs and outputs of one run live. Fixtures and real data use the same class."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    root: Path = Path(".")
    # v1 / v2 StructureDefinition files, and capability statements
    defs_v1: list[Path] = field(default_factory=list)
    defs_v2: list[Path] = field(default_factory=list)
    cap_v1: Path | None = None
    cap_v2: Path | None = None
    # resource-type name lists (optional) used to spot resources that no longer exist
    types_v1: Path | None = None
    types_v2: Path | None = None
    # profile files (CMS Blue Button IG for v1, CARIN BB IG for v2) and HL7 R3->R4 version maps
    profiles_v1: list[Path] = field(default_factory=list)
    profiles_v2: list[Path] = field(default_factory=list)
    map_files: list[Path] = field(default_factory=list)
    docs_dir: Path = Path("docs/v1")
    samples: list[Path] = field(default_factory=list)
    style_rules: Path | None = None
    reports_dir: Path = Path("reports")
    fixes_dir: Path = Path("fixes")
    publish_dir: Path = Path("publish")
    audit_file: Path = Path("audit/audit-log.jsonl")

    @classmethod
    def real(cls, root: str | Path = ".") -> "Config":
        from .settings import load_settings
        r = Path(root)
        st = load_settings(r)
        d = r / st.spec_dir
        names = ["patient", "coverage", "explanationofbenefit"]
        return cls(
            root=r,
            defs_v1=[d / f"STU3-{n}.json" for n in names],
            defs_v2=[d / f"R4-{n}.json" for n in names],
            cap_v1=r / "data/v1/capability.json",
            cap_v2=r / "data/v2/capability.json",
            types_v1=d / "resource-types-STU3.json",
            types_v2=d / "resource-types-R4.json",
            profiles_v1=sorted((d / "bluebutton-ig-stu3").glob("*.json")),
            profiles_v2=sorted((d / "carin-bb-r4").glob("*.json")),
            map_files=sorted((d / "maps").glob("*.html")),
            docs_dir=r / st.docs_dir,
            samples=sorted((r / "data/v1").glob("sample-*.json")),
            style_rules=r / st.style_rules,
            reports_dir=r / st.reports_dir,
            fixes_dir=r / st.fixes_dir,
            publish_dir=r / st.publish_dir,
            audit_file=r / st.audit_file,
        )

    @classmethod
    def fixtures(cls, fx: str | Path, out: str | Path) -> "Config":
        f, o = Path(fx), Path(out)
        return cls(
            root=o,
            defs_v1=sorted((f / "defs-v1").glob("*.json")),
            defs_v2=sorted((f / "defs-v2").glob("*.json")),
            cap_v1=f / "capability-v1.json",
            cap_v2=f / "capability-v2.json",
            types_v1=f / "types-v1.json",
            types_v2=f / "types-v2.json",
            profiles_v1=sorted((f / "profiles-v1").glob("*.json")),
            profiles_v2=sorted((f / "profiles-v2").glob("*.json")),
            map_files=sorted((f / "maps").glob("*.html")),
            docs_dir=f / "docs-v1",
            samples=sorted((f / "docs-v1").glob("sample-*.json")),
            style_rules=f / "style.yml",
            reports_dir=o / "reports",
            fixes_dir=o / "fixes",
            publish_dir=o / "publish",
            audit_file=o / "audit/audit-log.jsonl",
        )

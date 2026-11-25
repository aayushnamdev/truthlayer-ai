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
    docs_dir: Path = Path("docs/v1")
    samples: list[Path] = field(default_factory=list)
    style_rules: Path | None = None
    reports_dir: Path = Path("reports")
    fixes_dir: Path = Path("fixes")
    publish_dir: Path = Path("publish")
    audit_file: Path = Path("audit/audit-log.jsonl")

    @classmethod
    def real(cls, root: str | Path = ".") -> "Config":
        r = Path(root)
        d = r / "data/fhir-defs"
        names = ["patient", "coverage", "explanationofbenefit"]
        return cls(
            root=r,
            defs_v1=[d / f"STU3-{n}.json" for n in names],
            defs_v2=[d / f"R4-{n}.json" for n in names],
            cap_v1=r / "data/v1/capability.json",
            cap_v2=r / "data/v2/capability.json",
            types_v1=d / "resource-types-STU3.json",
            types_v2=d / "resource-types-R4.json",
            docs_dir=r / "docs/v1",
            samples=sorted((r / "data/v1").glob("sample-*.json")),
            style_rules=r / "rules/healthplan-style.yml",
            reports_dir=r / "reports",
            fixes_dir=r / "fixes",
            publish_dir=r / "publish",
            audit_file=r / "audit/audit-log.jsonl",
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
            docs_dir=f / "docs-v1",
            samples=sorted((f / "docs-v1").glob("sample-*.json")),
            style_rules=f / "style.yml",
            reports_dir=o / "reports",
            fixes_dir=o / "fixes",
            publish_dir=o / "publish",
            audit_file=o / "audit/audit-log.jsonl",
        )

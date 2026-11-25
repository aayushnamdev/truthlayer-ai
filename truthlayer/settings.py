"""Settings from truthlayer.yml, validated. The API key is NEVER read from or written to this file."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")


class SettingsError(ValueError):
    pass


@dataclass
class AISettings:
    model: str = "claude-haiku-5-5"
    allowed_models: list[str] = field(default_factory=lambda: ["claude-haiku-5-5"])
    cost_limit_usd: float = 1.0
    max_calls: int = 25
    max_output_tokens: int = 400
    max_passage_chars: int = 900
    fix_severities: list[str] = field(default_factory=lambda: ["CRITICAL", "HIGH"])
    retries: int = 2
    backoff_seconds: float = 1.5
    price_in_per_mtok: float = 1.0
    price_out_per_mtok: float = 5.0
    price_safety_multiplier: float = 2.0
    chars_per_token_estimate: float = 3.0


@dataclass
class Settings:
    docs_dir: str = "docs/v1"
    reports_dir: str = "reports"
    fixes_dir: str = "fixes"
    publish_dir: str = "publish"
    audit_file: str = "audit/audit-log.jsonl"
    style_rules: str = "rules/healthplan-style.yml"
    spec_dir: str = "data/fhir-defs"
    ai: AISettings = field(default_factory=AISettings)
    fail_on_severity: str = "CRITICAL"
    max_fix_first: int = 15


def _num(d: dict[str, Any], key: str, lo: float, hi: float, default: float) -> float:
    v = d.get(key, default)
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not (lo <= v <= hi):
        raise SettingsError(f"truthlayer.yml: ai.{key} must be a number between {lo} and {hi}, got {v!r}")
    return float(v)


def load_settings(root: str | Path = ".", env: dict[str, str] | None = None) -> Settings:
    env = dict(os.environ) if env is None else env
    p = Path(root) / "truthlayer.yml"
    s = Settings()
    if p.exists():
        try:
            raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise SettingsError(f"{p} is not valid YAML: {exc}") from None
        if not isinstance(raw, dict):
            raise SettingsError(f"{p} must contain a mapping at the top level")
        for k, v in (raw.get("paths") or {}).items():
            if not hasattr(s, k) or k in ("ai",):
                raise SettingsError(f"truthlayer.yml: unknown path setting '{k}'")
            setattr(s, k, str(v))
        a = raw.get("ai") or {}
        unknown = set(a) - set(AISettings.__dataclass_fields__)
        if unknown:
            raise SettingsError(f"truthlayer.yml: unknown ai setting(s): {', '.join(sorted(unknown))}")
        ai = s.ai
        ai.model = str(a.get("model", ai.model))
        ai.allowed_models = [str(x) for x in a.get("allowed_models", ai.allowed_models)]
        ai.cost_limit_usd = _num(a, "cost_limit_usd", 0.0, 1000.0, ai.cost_limit_usd)
        ai.max_calls = int(_num(a, "max_calls", 0, 10000, ai.max_calls))
        ai.max_output_tokens = int(_num(a, "max_output_tokens", 1, 8192, ai.max_output_tokens))
        ai.max_passage_chars = int(_num(a, "max_passage_chars", 50, 20000, ai.max_passage_chars))
        ai.retries = int(_num(a, "retries", 0, 10, ai.retries))
        ai.backoff_seconds = _num(a, "backoff_seconds", 0.0, 120.0, ai.backoff_seconds)
        ai.price_in_per_mtok = _num(a, "price_in_per_mtok", 0.0, 1000.0, ai.price_in_per_mtok)
        ai.price_out_per_mtok = _num(a, "price_out_per_mtok", 0.0, 1000.0, ai.price_out_per_mtok)
        ai.price_safety_multiplier = _num(a, "price_safety_multiplier", 1.0, 100.0, ai.price_safety_multiplier)
        ai.chars_per_token_estimate = _num(a, "chars_per_token_estimate", 1.0, 10.0, ai.chars_per_token_estimate)
        ai.fix_severities = [str(x).upper() for x in a.get("fix_severities", ai.fix_severities)]
        for sv in ai.fix_severities:
            if sv not in SEVERITIES:
                raise SettingsError(f"truthlayer.yml: ai.fix_severities has unknown severity '{sv}'")
        t = raw.get("thresholds") or {}
        s.fail_on_severity = str(t.get("fail_on_severity", s.fail_on_severity)).upper()
        if s.fail_on_severity not in (*SEVERITIES, "NONE"):
            raise SettingsError("truthlayer.yml: thresholds.fail_on_severity must be CRITICAL, HIGH, MEDIUM, LOW or NONE")
        s.max_fix_first = int(t.get("max_fix_first", s.max_fix_first))
    override = env.get("TRUTHLAYER_MODEL")
    if override:
        s.ai.model = override
    if s.ai.model not in s.ai.allowed_models:
        raise SettingsError(f"model '{s.ai.model}' is not in ai.allowed_models {s.ai.allowed_models}")
    return s


def load_dotenv(root: str | Path = ".") -> int:
    """Read KEY=VALUE lines from <root>/.env into the environment (never overrides, never prints values)."""
    p = Path(root) / ".env"
    if not p.exists():
        return 0
    n = 0
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip("\"'")
        if k and v and k not in os.environ:
            os.environ[k] = v
            n += 1
    return n

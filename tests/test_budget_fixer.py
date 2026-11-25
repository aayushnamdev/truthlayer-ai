"""The fixer with a FAKE client. No test ever calls the real API."""
import json
import types

import pytest

from truthlayer import fixer
from truthlayer.budget import Budget, BudgetExceeded
from truthlayer.settings import AISettings, Settings, SettingsError, load_settings


class FakeClient:
    def __init__(self, fail_first=0, reply=None, tin=300, tout=60, exc=None):
        self.calls, self.kwargs, self.fail_first, self.tin, self.tout, self.exc = 0, [], fail_first, tin, tout, exc
        self.reply = reply or '{"revised_passage": "fixed text", "reason": "because"}'
        self.messages = types.SimpleNamespace(create=self.create)

    def create(self, **kw):
        self.calls += 1
        self.kwargs.append(kw)
        if self.calls <= self.fail_first:
            raise (self.exc or RuntimeError("temporary failure"))
        return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text=self.reply)],
                                     usage=types.SimpleNamespace(input_tokens=self.tin, output_tokens=self.tout))


def settings(**ai):
    s = Settings()
    for k, v in ai.items():
        setattr(s.ai, k, v)
    return s


def test_only_haiku_allowed(monkeypatch):
    monkeypatch.setenv("TRUTHLAYER_MODEL", "claude-opus-5-5")
    with pytest.raises(SettingsError, match="allowed_models"):
        load_settings(".")


def test_settings_validation(tmp_path):
    (tmp_path / "truthlayer.yml").write_text("ai:\n  cost_limit_usd: -3\n")
    with pytest.raises(SettingsError, match="cost_limit_usd"):
        load_settings(tmp_path)
    (tmp_path / "truthlayer.yml").write_text("ai:\n  bogus: 1\n")
    with pytest.raises(SettingsError, match="unknown ai setting"):
        load_settings(tmp_path)
    (tmp_path / "truthlayer.yml").write_text(": : :\n  - [")
    with pytest.raises(SettingsError, match="not valid YAML"):
        load_settings(tmp_path)


def test_repo_settings_enforce_the_budget_rules():
    s = load_settings(".")
    assert (s.ai.model, s.ai.cost_limit_usd, s.ai.max_calls, s.ai.max_output_tokens) == ("claude-haiku-5-5", 1.0, 25, 400)
    assert s.ai.fix_severities == ["CRITICAL", "HIGH"]


def test_live_run_only_fixes_critical_and_high_with_small_prompts(analysis, cfg):
    fc = FakeClient()
    d = fixer.propose_fixes(analysis, cfg, settings(), live=True, client=fc)
    sev = {f.id: f.severity for f in analysis.findings}
    assert d["proposals"] and all(sev[p["finding_id"]] in ("CRITICAL", "HIGH") for p in d["proposals"])
    assert all(k["max_tokens"] == 400 and k["model"] == "claude-haiku-5-5" for k in fc.kwargs)
    assert all(len(k["messages"][0]["content"]) < 2000 for k in fc.kwargs)
    assert d["meta"]["mode"] == "LIVE" and d["meta"]["input_tokens"] == 300 * fc.calls


def test_call_cap(analysis, cfg):
    fc = FakeClient()
    d = fixer.propose_fixes(analysis, cfg, settings(max_calls=2), live=True, client=fc)
    assert fc.calls == 2 and "call limit" in d["meta"]["stopped"]


def test_cost_limit_stops_before_the_call(analysis, cfg):
    fc = FakeClient()
    d = fixer.propose_fixes(analysis, cfg, settings(cost_limit_usd=0.0001), live=True, client=fc)
    assert fc.calls == 0 and "exceed" in d["meta"]["stopped"]
    assert d["meta"]["budget"]["charged_usd"] <= 0.0001


def test_budget_never_exceeded_over_many_calls(analysis, cfg):
    fc = FakeClient(tin=2000, tout=400)
    s = settings(cost_limit_usd=0.02)
    fixer.propose_fixes(analysis, cfg, s, live=True, client=fc)
    b = Budget(cfg.fixes_dir / "cost-ledger.json", s.ai)
    assert b.spent <= 0.02 and b.data["calls"] == fc.calls


def test_retries_with_backoff_count_toward_budget(analysis, cfg):
    fc = FakeClient(fail_first=2)
    slept = []
    d = fixer.propose_fixes(analysis, cfg, settings(max_calls=3, retries=2), live=True, client=fc, sleep=slept.append)
    assert fc.calls == 3 and slept == [1.5, 3.0]                 # exponential backoff
    ledger = json.loads((cfg.fixes_dir / "cost-ledger.json").read_text())
    assert ledger["calls"] == 3 and [e["ok"] for e in ledger["entries"]] == [False, False, True]
    assert d["proposals"][0]["proposed"] == "fixed text"


def test_failed_attempts_are_charged_even_without_usage(analysis, cfg):
    fc = FakeClient(fail_first=99)
    d = fixer.propose_fixes(analysis, cfg, settings(max_calls=3, retries=2), live=True, client=fc, sleep=lambda s: None)
    ledger = json.loads((cfg.fixes_dir / "cost-ledger.json").read_text())
    assert ledger["spent_usd"] > 0 and ledger["calls"] == 3
    assert d["proposals"] and not d["proposals"][0]["changed"]


def test_api_key_never_appears_in_outputs(analysis, cfg, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-SUPERSECRETVALUE1234")
    fc = FakeClient(fail_first=99, exc=RuntimeError("auth failed for key sk-ant-api03-SUPERSECRETVALUE1234"))
    fixer.propose_fixes(analysis, cfg, settings(max_calls=2, retries=1), live=True, client=fc, sleep=lambda s: None)
    blob = "".join(p.read_text() for p in cfg.fixes_dir.glob("*.json")) + cfg.audit_file.read_text()
    assert "SUPERSECRET" not in blob
    assert "SUPERSECRET" not in fixer.scrub("oops sk-ant-api03-SUPERSECRETVALUE1234")


def test_live_without_key_falls_back_to_mock(analysis, cfg):
    d = fixer.propose_fixes(analysis, cfg, settings(), live=True)
    assert d["meta"]["mode"] == "MOCK" and d["meta"]["estimated_cost_usd"] == 0


def test_unparseable_reply_keeps_original(analysis, cfg):
    fc = FakeClient(reply="not json")
    d = fixer.propose_fixes(analysis, cfg, settings(max_calls=1), live=True, client=fc)
    assert not d["proposals"][0]["changed"]


def test_ai_test_makes_one_call(analysis, cfg):
    fc = FakeClient(tin=410, tout=33)
    r = fixer.ai_test(analysis, cfg, settings(), client=fc)
    assert fc.calls == 1 and r["input_tokens"] == 410 and r["output_tokens"] == 33
    assert r["budget_remaining_usd"] < 1.0


def test_propose_one_mock_and_live(analysis, cfg):
    fid = next(f.id for f in analysis.findings if f.severity == "CRITICAL" and f.locations)
    p = fixer.propose_one(analysis, cfg, settings(), fid)
    assert p["mode"] == "MOCK" and p["status"] == "PENDING"
    fc = FakeClient()
    p2 = fixer.propose_one(analysis, cfg, settings(), fid, live=True, client=fc)
    assert p2["mode"] == "LIVE" and fc.calls == 1
    props = json.loads((cfg.fixes_dir / "proposals.json").read_text())["proposals"]
    assert len([x for x in props if x["finding_id"] == fid]) == 1


def test_budget_ledger_persists_and_detects_damage(tmp_path):
    ai = AISettings()
    b = Budget(tmp_path / "l.json", ai)
    b.charge("x", 100, 50, 0.01, True)
    assert Budget(tmp_path / "l.json", ai).data["calls"] == 1
    (tmp_path / "l.json").write_text("{broken")
    with pytest.raises(ValueError, match="damaged"):
        Budget(tmp_path / "l.json", ai)
    b2 = Budget(tmp_path / "m.json", AISettings(cost_limit_usd=0.001))
    with pytest.raises(BudgetExceeded):
        b2.check(0.01)

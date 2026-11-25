"""Part B: dashboard helpers and page, CLI behaviour, workflows, packaging files. No real API calls."""
import json
import logging
import os
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from truthlayer import cli, fixer, logging_setup
from truthlayer import dashboard_data as dd
from truthlayer.drift import write_reports
from truthlayer.settings import load_dotenv

REPO = Path(__file__).resolve().parent.parent


# ---------- dashboard data helpers
@pytest.fixture
def report(analysis, cfg):
    _, js = write_reports(analysis, cfg)
    return json.loads(js.read_text())


def test_filter_findings(report):
    crit = dd.filter_findings(report["findings"], ["CRITICAL"])
    assert crit and all(f["severity"] == "CRITICAL" for f in crit)
    ghosts = dd.filter_findings(report["findings"], None, ["GHOST"])
    assert {f["label"] for f in ghosts} == {"GHOST"}
    assert [f["v1_element"] for f in dd.filter_findings(report["findings"], None, None, "nickname")] == ["Patient.nickname"]
    sevs = [f["severity"] for f in dd.filter_findings(report["findings"])]
    assert sevs == sorted(sevs, key=dd.SEVERITIES.index)          # most severe first


def test_score_cards(report):
    cards = dd.score_cards(report, {"caught": 32, "n": 35}, 0.6, 0.0)
    assert cards["cms_recall"] == "32/35" and cards["cms_recall_pct"] == 91
    assert cards["real_drift_found"] == sum(1 for f in report["findings"] if f["label"] != "UNVERIFIABLE")
    assert dd.score_cards(report, None, None, None)["cms_recall"] == "n/a"


def test_mark_diff_highlights_only_the_difference():
    old, new = dd.mark_diff("the service field", "the productOrService field")
    assert "<mark" in old and "service" in old and "<mark" in new and "productOrService" in new
    assert "the" in old and "<mark style=\"background:#fecdca\">the</mark>" not in old


def test_highlight_escapes_html():
    out = dd.highlight_tokens("<b>nick</b> name", ["nick"])
    assert "<b>" not in out and "&lt;b&gt;" in out and "<mark" in out


def test_booklet_context_and_audit_reader(analysis, cfg, report):
    f = next(x for x in report["findings"] if x["label"] == "GHOST" and x["v1_element"] == "Patient.nickname")
    text, lo = dd.booklet_context(REPO, f["locations"][0])
    assert "nickname" in text and lo >= 1
    rows = dd.read_audit(cfg.audit_file)
    assert rows and rows[0]["time"] >= rows[-1]["time"]
    assert all(r["action"] == "finding" for r in dd.read_audit(cfg.audit_file, "finding"))


def test_zip_pages(analysis, cfg):
    from truthlayer import publisher
    publisher.publish(analysis, cfg, None)
    import io
    import zipfile
    names = zipfile.ZipFile(io.BytesIO(dd.zip_pages(cfg.publish_dir))).namelist()
    assert "llms.txt" in names and any(n.startswith("pages/") for n in names)


# ---------- dashboard page
def test_dashboard_loads_without_calling_the_ai(monkeypatch):
    from streamlit.testing.v1 import AppTest

    def boom(*a, **k):
        raise AssertionError("the dashboard called the AI on page load")

    monkeypatch.setattr(fixer.LiveClient, "call", boom)
    monkeypatch.setattr(fixer, "propose_fixes", boom)
    monkeypatch.setattr(fixer, "propose_one", boom)
    monkeypatch.setenv("TRUTHLAYER_ROOT", str(REPO))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    at = AppTest.from_file(str(REPO / "truthlayer" / "dashboard.py"), default_timeout=30).run()
    assert not at.exception
    assert [t.value for t in at.title] == ["TruthLayer AI"]
    assert any("MOCK mode" in m.value for m in at.sidebar.markdown)          # MOCK is shown clearly
    for page in ("Overview", "Fix these first", "Finding detail", "Downloads", "Audit log"):
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception, page


# ---------- CLI
def fake_cfg(monkeypatch, cfg):
    monkeypatch.setattr(cli.Config, "real", classmethod(lambda c, root=".": cfg))


def test_check_fails_on_critical_and_can_be_configured(monkeypatch, cfg):
    fake_cfg(monkeypatch, cfg)
    r = CliRunner().invoke(cli.main, ["check"])
    assert r.exit_code == 1 and "FAIL" in r.output
    r = CliRunner().invoke(cli.main, ["check", "--fail-on", "NONE"])
    assert r.exit_code == 0 and "by severity" in r.output


def test_clear_error_for_invalid_file(monkeypatch, cfg, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{oops")
    cfg.defs_v1 = [bad]
    fake_cfg(monkeypatch, cfg)
    r = CliRunner().invoke(cli.main, ["check"])
    assert r.exit_code == 2 and "Error:" in r.output and "not valid JSON" in r.output and "Traceback" not in r.output


def test_clear_error_for_missing_docs(monkeypatch, cfg, tmp_path):
    cfg.docs_dir = tmp_path / "nope"
    fake_cfg(monkeypatch, cfg)
    r = CliRunner().invoke(cli.main, ["check"])
    assert r.exit_code == 2 and "docs folder not found" in r.output


def test_fix_without_key_says_mock(monkeypatch, cfg):
    fake_cfg(monkeypatch, cfg)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = CliRunner().invoke(cli.main, ["fix", "--live"])
    assert r.exit_code == 0 and "Mode: MOCK" in r.output


def test_fix_is_mock_even_with_a_key_unless_live(monkeypatch, cfg):
    fake_cfg(monkeypatch, cfg)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-real-0000")

    def boom(*a, **k):
        raise AssertionError("AI must not be called without --live")

    monkeypatch.setattr(fixer.LiveClient, "call", boom)
    r = CliRunner().invoke(cli.main, ["fix"])
    assert r.exit_code == 0 and "Mode: MOCK" in r.output


def test_ai_test_needs_a_key(monkeypatch, cfg):
    fake_cfg(monkeypatch, cfg)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = CliRunner().invoke(cli.main, ["ai-test"])
    assert r.exit_code == 2 and "ANTHROPIC_API_KEY is not set" in r.output


def test_unknown_proposal_is_a_clear_error(monkeypatch, cfg):
    fake_cfg(monkeypatch, cfg)
    CliRunner().invoke(cli.main, ["fix"])
    r = CliRunner().invoke(cli.main, ["approve", "P-999"])
    assert r.exit_code == 2 and "P-999" in r.output


def test_dotenv_loads_without_overriding(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("# c\nFOO_TL=bar\nTL_KEEP=new\nEMPTY=\n")
    monkeypatch.setenv("TL_KEEP", "old")
    monkeypatch.delenv("FOO_TL", raising=False)
    assert load_dotenv(tmp_path) == 1
    assert os.environ["FOO_TL"] == "bar" and os.environ["TL_KEEP"] == "old"
    monkeypatch.delenv("FOO_TL", raising=False)


# ---------- logging
def test_logs_never_contain_the_key(monkeypatch, capsys):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api03-HIDEMEPLEASE123456")
    logging_setup.setup(json_logs=True, level="INFO")
    logging.getLogger("truthlayer.test").warning("failed with key sk-ant-api03-HIDEMEPLEASE123456")
    err = capsys.readouterr().err
    assert "HIDEME" not in err and "[hidden]" in err
    assert json.loads(err.strip().splitlines()[-1])["level"] == "WARNING"


# ---------- packaging and workflows
def test_workflows_are_valid_and_safe():
    ci = yaml.safe_load((REPO / ".github/workflows/ci.yml").read_text())
    steps = " ".join(s.get("run", "") for s in ci["jobs"]["test"]["steps"])
    assert "pytest" in steps and "ruff" in steps and "mypy" in steps
    assert ci["jobs"]["test"]["env"]["ANTHROPIC_API_KEY"] == ""
    chk_text = (REPO / ".github/workflows/truthlayer-check.yml").read_text()
    chk = yaml.safe_load(chk_text)
    on = chk.get("on") or chk[True]
    assert "data/**" in on["pull_request"]["paths"] and "docs/**" in on["push"]["paths"]
    job = chk["jobs"]["check"]
    assert job["env"]["ANTHROPIC_API_KEY"] == ""                       # MOCK mode only
    assert any("upload-artifact" in s.get("uses", "") for s in job["steps"])
    assert "GITHUB_STEP_SUMMARY" in chk_text and "TRUTHLAYER_FAIL_ON" in chk_text and "fail_on" in chk_text


def test_secrets_are_not_committed_or_baked_in():
    gi = (REPO / ".gitignore").read_text().split()
    assert ".env" in gi and "secrets/" in gi
    env = (REPO / ".env.example").read_text()
    assert "ANTHROPIC_API_KEY=\n" in env and "sk-ant" not in env
    assert "sk-ant" not in (REPO / "Dockerfile").read_text()
    assert "COPY .env" not in (REPO / "Dockerfile").read_text()


def test_makefile_targets_and_config_file():
    mk = (REPO / "Makefile").read_text()
    for target in ("install:", "test:", "run:", "app:", "demo:"):
        assert target in mk
    cfg = yaml.safe_load((REPO / "truthlayer.yml").read_text())
    assert cfg["ai"]["cost_limit_usd"] == 1.0 and cfg["ai"]["max_calls"] == 25
    assert "api_key" not in json.dumps(cfg).lower()
    py = (REPO / "pyproject.toml").read_text()
    assert "streamlit==" in py and "anthropic==" in py and ">=" not in py.split("dependencies = [")[1].split("]")[0]


def test_no_license_file_added():
    assert not (REPO / "LICENSE").exists() and not (REPO / "LICENSE.md").exists()

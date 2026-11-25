import json

from click.testing import CliRunner

from truthlayer.cli import main
from truthlayer.score import score


def test_demo_runs_on_fixtures(tmp_path):
    r = CliRunner().invoke(main, ["demo", "--out", str(tmp_path / "d")])
    assert r.exit_code == 0, r.output
    assert "SYNTHETIC DEMO" in r.output and "GHOST" in r.output and "MOCK" in r.output
    assert (tmp_path / "d/publish/llms.txt").exists() and (tmp_path / "d/audit/audit-log.jsonl").exists()


def test_version_and_help():
    r = CliRunner().invoke(main, ["--help"])
    for cmd in ("check", "fix", "review", "approve", "reject", "publish", "run", "demo", "serve-mcp", "style", "score"):
        assert cmd in r.output


def test_score_with_synthetic_truth(tmp_path):
    rep = {"findings": [{"id": "F-1", "label": "WRONG", "v1_element": "Patient.phoneNumber", "v2_element": "Patient.phone"},
                        {"id": "F-2", "label": "MISSING", "v1_element": "", "v2_element": "Patient.zzz"}],
           "spec_changes": [{"v1_path": "Patient.gone", "v2_path": "", "kind": "REMOVED"}]}
    (tmp_path / "r.json").write_text(json.dumps(rep))
    (tmp_path / "t.csv").write_text("change_id,resource,v1_element,v2_element,change_type,source_url,evidence\n"
                                    "C1,Patient,Patient.phoneNumber,Patient.phone,renamed,u,e\n"
                                    "C2,Patient,Patient.gone,,removed,u,e\n"
                                    "C3,Patient,Patient.never,,removed,u,e\n")
    s = score(tmp_path / "t.csv", tmp_path / "r.json")
    assert [r["status"] for r in s["rows"]] == ["caught", "in-spec-diff-only", "missed"]
    assert s["precision"] == 0.5 and s["caught"] == 1

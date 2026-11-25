import json
import pytest
from truthlayer import approval, audit, fixer


def make(analysis, cfg):
    return fixer.propose_fixes(analysis, cfg)


def test_mock_mode_without_key(analysis, cfg):
    assert fixer.mode() == "MOCK"
    d = make(analysis, cfg)
    assert d["meta"]["mode"] == "MOCK" and d["meta"]["estimated_cost_usd"] == 0
    assert d["proposals"] and all(p["status"] == "PENDING" for p in d["proposals"])
    assert (cfg.fixes_dir / "proposals.json").exists()


def test_prompt_contains_only_passage_and_definition():
    pr = fixer.build_prompt("old text", "Patient.phone [0..1] type=string", "renamed", "phoneNumber", "phone")
    assert "old text" in pr and "Patient.phone" in pr
    assert "http" not in pr and "docs/" not in pr


def test_mock_rename_edit(analysis, cfg):
    d = make(analysis, cfg)
    p = next(x for x in d["proposals"] if x["element"] == "Patient.phoneNumber")
    assert "phone" in p["proposed"] and p["changed"] and p["confidence"] == "LOW"


def test_nothing_changes_without_approval(analysis, cfg):
    make(analysis, cfg)
    assert all(p["status"] == "PENDING" for p in approval.load(cfg)["proposals"])


def test_approve_and_reject_are_audited(analysis, cfg):
    d = make(analysis, cfg)
    ids = [p["id"] for p in d["proposals"]]
    approval.set_status(cfg, ids[0], "APPROVED", "alice")
    approval.set_status(cfg, ids[1], "REJECTED", "bob")
    st = {p["id"]: (p["status"], p["approver"]) for p in approval.load(cfg)["proposals"]}
    assert st[ids[0]] == ("APPROVED", "alice") and st[ids[1]] == ("REJECTED", "bob")
    acts = [(r["action"], r["approver"]) for r in audit.read(cfg.audit_file)]
    assert ("approval", "alice") in acts and ("rejection", "bob") in acts


def test_auto_approve_only_high_and_changed(analysis, cfg):
    make(analysis, cfg)
    done = approval.auto_approve_high(cfg)
    props = {p["id"]: p for p in approval.load(cfg)["proposals"]}
    assert done
    for pid, p in props.items():
        if p["status"] == "APPROVED":
            assert p["confidence"] == "HIGH" and p["changed"] and p["approver"] == "auto"
        if p["confidence"] == "LOW":
            assert p["status"] == "PENDING"
    assert any(r["approver"] == "auto" for r in audit.read(cfg.audit_file))


def test_unknown_proposal(analysis, cfg):
    make(analysis, cfg)
    with pytest.raises(KeyError):
        approval.set_status(cfg, "P-999", "APPROVED", "x")


def test_review_text(analysis, cfg):
    make(analysis, cfg)
    t = approval.review_text(cfg)
    assert "Mode: MOCK" in t and "P-001" in t

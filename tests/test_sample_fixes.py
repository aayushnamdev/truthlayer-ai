"""Part 1: small checked edits for JSON samples, and publishing corrected samples. FAKE client only."""
import json
import types

import pytest

from truthlayer import approval, fixer, publisher, sample_edit
from truthlayer.settings import Settings


class EditClient:
    """Answers the edit prompt (system mentions 'samples') or the rewrite prompt."""

    def __init__(self, edit=None, rewrite=None, tin=250, tout=40):
        self.edit, self.rewrite, self.tin, self.tout = edit, rewrite, tin, tout
        self.calls = []
        self.messages = types.SimpleNamespace(create=self.create)

    def create(self, **kw):
        self.calls.append(kw)
        body = self.edit if "samples" in kw["system"] else self.rewrite
        return types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text=json.dumps(body))],
                                     usage=types.SimpleNamespace(input_tokens=self.tin, output_tokens=self.tout))


RENAME = {"old_text": '"maritalStatus"', "new_text": '"maritalStatusText"', "reason": "v2 turns the code into text"}


def sample_prop(d):
    return next(p for p in d["proposals"] if p["kind"] == "sample" and p["element"] == "Patient.maritalStatus")


# ---- helpers
def test_apply_edit_rules():
    assert sample_edit.apply_edit("a b a", "b", "c") == ("a c a", "")
    assert "appears 2 times" in sample_edit.apply_edit("a b a", "a", "c")[1]
    assert "not found" in sample_edit.apply_edit("abc", "z", "c")[1]
    assert sample_edit.apply_edit("abc", "", "") == ("abc", "")          # empty edit = nothing to change


def test_parse_edit_reply():
    assert sample_edit.parse_edit_reply('x {"old_text":"a","new_text":"b","reason":"r"} y') == ("a", "b", "r", "")
    assert sample_edit.parse_edit_reply("nope")[3] == "unparseable reply"
    assert sample_edit.parse_edit_reply('{"old_text": 5}')[3] == "unparseable reply"
    long = " ".join(["w"] * 60)
    assert len(sample_edit.parse_edit_reply(json.dumps({"old_text": "", "new_text": "", "reason": long}))[2].split()) == 30


def test_json_validation():
    whole = '{\n  "a": {\n    "b": 1\n  }\n}'
    assert sample_edit.validate_file_edit(whole, 2, 2, '  "z": {') == ""
    assert "invalid JSON" in sample_edit.validate_file_edit(whole, 2, 2, '  "z": [')
    assert sample_edit.validate_fragment_edit('"a": {"b": 1}', '"c": {"b": 1}') == ""
    assert "invalid" in sample_edit.validate_fragment_edit('"a": {"b": 1}', '"a": {"b": 1')
    # a fragment that is not JSON on its own: bracket and quote balance must not change
    assert sample_edit.validate_fragment_edit('"a": {\n "b": [', '"c": {\n "b": [') == ""
    assert "balance" in sample_edit.validate_fragment_edit('"a": {\n "b": [', '"c": {\n "b": ')


def test_edit_from_rewrite_round_trips():
    o = 'x\n"service": {\n  "a": 1\n}'
    p = o.replace('"service"', '"productOrService"')
    e = sample_edit.edit_from_rewrite(o, p)
    assert sample_edit.apply_edit(o, e["old_text"], e["new_text"])[0] == p
    assert sample_edit.edit_from_rewrite(o, o) is None


# ---- fixer in edit mode
def test_sample_passages_use_the_small_edit_prompt(analysis, cfg):
    fc = EditClient(edit=RENAME, rewrite={"revised_passage": "x", "reason": "y"})
    d = fixer.propose_fixes(analysis, cfg, Settings(), live=True, client=fc)
    p = sample_prop(d)
    assert p["format"] == "edit" and p["changed"] and p["edit"]["old_text"] == '"maritalStatus"'
    assert '"maritalStatusText"' in p["proposed"] and p["proposed"].count("maritalStatus") == 1
    assert p["reason"] == "v2 turns the code into text"
    sample_calls = [c for c in fc.calls if "samples" in c["system"]]
    assert sample_calls and all(c["max_tokens"] == 400 and c["model"] == "claude-haiku-5-5" for c in fc.calls)
    prose = next(x for x in d["proposals"] if x["kind"] == "prose")
    assert prose["format"] == "rewrite"


@pytest.mark.parametrize("bad, why", [
    ({"old_text": '"notThere"', "new_text": "x", "reason": "r"}, "not found"),
    ({"old_text": "{", "new_text": "", "reason": "r"}, "must be unique"),
    ({"old_text": '"coding": [', "new_text": '"coding": ', "reason": "r"}, "invalid JSON"),
])
def test_bad_edits_are_rejected(analysis, cfg, bad, why):
    d = fixer.propose_fixes(analysis, cfg, Settings(), live=True, client=EditClient(edit=bad, rewrite={"revised_passage": "", "reason": ""}))
    p = sample_prop(d)
    assert not p["changed"] and p["reason"].startswith("edit rejected") and why in p["reason"]


def test_retry_uses_edit_format_and_its_own_caps(analysis, cfg):
    bad = EditClient(edit={"nonsense": 1}, rewrite={"revised_passage": "x", "reason": "y"})
    # first run: the model answers samples with something unusable
    bad.create = lambda **kw: types.SimpleNamespace(content=[types.SimpleNamespace(type="text", text="garbage")],
                                                    usage=types.SimpleNamespace(input_tokens=200, output_tokens=400))
    bad.messages = types.SimpleNamespace(create=bad.create)
    d = fixer.propose_fixes(analysis, cfg, Settings(), live=True, client=bad)
    assert any(p["kind"] == "sample" and p["reason"] == "unparseable reply" for p in d["proposals"])
    first_calls = json.loads((cfg.fixes_dir / "cost-ledger.json").read_text())["calls"]
    good = EditClient(edit=RENAME, rewrite=None)
    r = fixer.retry_unparseable(analysis, cfg, Settings(), client=good, extra_calls=20, extra_usd=0.05)
    assert r["retried"] == len(good.calls) <= 20 and r["charged_usd"] <= 0.05                # never more than the extra caps
    capped = fixer.retry_unparseable(analysis, cfg, Settings(), client=EditClient(edit=RENAME, rewrite=None), extra_calls=1)
    assert capped["retried"] <= 1
    assert any("samples" in c["system"] for c in good.calls)                                # samples use the small-edit prompt
    assert any("samples" not in c["system"] for c in good.calls)                            # prose keeps the rewrite prompt
    ledger = json.loads((cfg.fixes_dir / "cost-ledger.json").read_text())
    assert ledger["calls"] == first_calls + r["retried"] + capped["retried"] and ledger["limit_usd"] == 1.0   # normal limits restored in the file


def test_mock_sample_edit_renames_a_key(analysis, cfg):
    d = fixer.propose_fixes(analysis, cfg, Settings())
    rename = [p for p in d["proposals"] if p["kind"] == "sample" and p["changed"]]
    for p in rename:
        assert p["edit"] and p["mode"] == "MOCK"


# ---- publishing corrected samples
def approved(cfg, **kw):
    base = {"id": "P-900", "finding_id": "F-003", "label": "GHOST", "severity": "CRITICAL", "confidence": "HIGH",
            "status": "APPROVED", "mode": "LIVE", "model": "m", "kind": "sample", "element": "x", "v2_element": "",
            "original": "", "proposed": "", "changed": True, "reason": "r", "prompt_hash": "h", "input_tokens": 1,
            "output_tokens": 1, "approver": "tester", "format": "edit"}
    base.update(kw)
    return {"meta": {}, "proposals": [base]}


def test_corrected_sample_is_published_as_valid_json(analysis, cfg):
    file = "tests/fixtures/docs-v1/sample-patient.json"
    props = approved(cfg, file=file, line=9, end_line=11, edit={"old_text": '"nickname"', "new_text": '"alias"'},
                     publishable=False)          # the old flag is ignored: .json files are publishable now
    m = publisher.publish(analysis, cfg, props)
    out = cfg.publish_dir / "samples" / "sample-patient.json"
    assert out.exists()
    data = json.loads(out.read_text())
    assert "alias" in data and "nickname" not in data
    assert "nickname" in json.loads((cfg.root / file).read_text())        # the source file is untouched
    assert m["samples"][0]["valid_json"] and m["samples"][0]["fixes_applied"] == 1
    assert "samples/sample-patient.json" in (cfg.publish_dir / "llms.txt").read_text()


def test_unapproved_or_invalid_sample_edits_are_not_published(analysis, cfg):
    file = "tests/fixtures/docs-v1/sample-patient.json"
    pending = approved(cfg, file=file, line=9, end_line=11, status="PENDING",
                       edit={"old_text": '"nickname"', "new_text": '"alias"'})
    publisher.publish(analysis, cfg, pending)
    assert not list((cfg.publish_dir / "samples").glob("*.json"))
    broken = approved(cfg, file=file, line=9, end_line=11, edit={"old_text": '"nickname": "Sam",', "new_text": '"nickname": ,'})
    publisher.publish(analysis, cfg, broken)
    assert not list((cfg.publish_dir / "samples").glob("*.json"))
    from truthlayer import audit
    assert any(r["action"] == "publish_sample_rejected" for r in audit.read(cfg.audit_file))


def test_fenced_sample_edit_keeps_the_fences(analysis, cfg):
    p = next(x for x in fixer.propose_fixes(analysis, cfg, Settings())["proposals"] if x["kind"] == "sample" and x["file"].endswith(".md"))
    props = approved(cfg, file=p["file"], line=p["line"], end_line=p["end_line"],
                     edit={"old_text": '"maritalStatus"', "new_text": '"maritalStatusText"'})
    publisher.publish(analysis, cfg, props)
    page = next(x for x in (cfg.publish_dir / "pages").glob("*sample*.md")).read_text()
    assert "```json" in page and page.count("```") >= 2 and "maritalStatusText" in page


def test_dashboard_auto_approve_counts_json_samples(analysis, cfg):
    fixer.propose_fixes(analysis, cfg, Settings())
    ids = approval.auto_approve_high(cfg)
    props = {p["id"]: p for p in approval.load(cfg)["proposals"]}
    assert all(props[i]["file"].endswith((".md", ".json")) for i in ids)


def test_mock_run_never_overwrites_real_ai_proposals(analysis, cfg):
    fixer.propose_fixes(analysis, cfg, Settings(), live=True, client=EditClient(edit=RENAME, rewrite={"revised_passage": "x", "reason": "y"}))
    with pytest.raises(ValueError, match="real AI proposals"):
        fixer.propose_fixes(analysis, cfg, Settings())                       # MOCK
    kept = json.loads((cfg.fixes_dir / "proposals.json").read_text())
    assert kept["meta"]["mode"] == "LIVE"
    fixer.propose_fixes(analysis, cfg, Settings(), overwrite=True)           # only with the explicit flag
    assert json.loads((cfg.fixes_dir / "proposals.json").read_text())["meta"]["mode"] == "MOCK"


def test_old_rewrite_proposals_still_publish_as_edits(analysis, cfg):
    file = "tests/fixtures/docs-v1/sample-patient.json"
    props = approved(cfg, file=file, line=9, end_line=11, original='  "nickname": "Sam",', proposed='  "alias": "Sam",')
    publisher.publish(analysis, cfg, props)               # no 'edit' key: derived from the rewrite
    assert "alias" in json.loads((cfg.publish_dir / "samples" / "sample-patient.json").read_text())

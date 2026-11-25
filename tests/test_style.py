from truthlayer import style
from conftest import FX


def run():
    return style.check_file(FX / "docs-v1" / "patient-guide.md", style.load_rules(FX / "style.yml"), "patient-guide.md")


def test_member_not_patient():
    r = [x for x in run() if x["rule"] == "HP-001"]
    assert r and r[0]["line"] == 8 and "member" in r[0]["suggestion"]


def test_date_format_rule():
    assert any(x["rule"] == "HP-002" and "01/02/2020" in x["snippet"] for x in run())


def test_endpoint_section_needs_error_codes_and_sample():
    got = {x["rule"] for x in run()}
    assert "HP-004" in got and "HP-005" in got


def test_every_doc_states_versions():
    # the fixture does state them, so those rules must not fire
    got = {x["rule"] for x in run()}
    assert "HP-003" not in got and "HP-010" not in got

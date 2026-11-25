from collections import Counter
from truthlayer.drift import EXAMPLE, GHOST, MISSING, WRONG, write_reports
import json


def by(analysis):
    return {(f.label, f.v1_element or f.v2_element) for f in analysis.findings}


def test_all_four_labels_planted(analysis):
    got = by(analysis)
    assert (WRONG, "Patient.phoneNumber") in got            # prose names a probable rename
    assert (WRONG, "Patient.active") in got                 # table row, cardinality changed
    assert (EXAMPLE, "Patient.maritalStatus") in got        # only in a sample, type changed
    assert (GHOST, "Patient.nickname") in got               # described, gone in v2
    assert (GHOST, "Patient?legacy-id") in got
    assert (GHOST, "ReferralRequest") in got                # resource type absent from v2
    assert (MISSING, "Patient.mrn") in got                  # new in v2, never mentioned
    assert (MISSING, "Coverage.status") in got              # changed in v2, never mentioned


def test_confidence_rules(analysis):
    f = {x.v1_element or x.v2_element: x for x in analysis.findings}
    assert f["Patient.phoneNumber"].confidence == "LOW" and f["Patient.phoneNumber"].ask_human
    assert f["Patient.mrn"].confidence == "HIGH"            # required in v2
    assert f["Patient.preferredLanguage"].confidence == "LOW"   # optional addition
    assert f["Patient.active"].confidence == "HIGH"


def test_no_false_findings_for_unchanged_elements(analysis):
    elems = {x.v1_element for x in analysis.findings}
    assert "Patient.birthDate" not in elems and "Patient.name" not in {e for e in elems if e == "Patient.birthDate"}


def test_reports_written(analysis, cfg):
    md, js = write_reports(analysis, cfg)
    text = md.read_text()
    assert text.index("In plain English") < text.index("## WRONG")
    data = json.loads(js.read_text())
    assert data["summary"]["findings"] == len(analysis.findings)
    assert data["findings"][0]["locations"] is not None

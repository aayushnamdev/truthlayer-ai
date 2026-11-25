from conftest import FX

from truthlayer.fhir_adapter import load_capability, load_definitions
from truthlayer.specdiff import ADDED, CHANGED, POSSIBLE_RENAME, REMOVED, run_diff


def diff():
    v1 = load_definitions(sorted((FX / "defs-v1").glob("*.json")))
    v2 = load_definitions(sorted((FX / "defs-v2").glob("*.json")))
    return run_diff(v1, v2, load_capability(FX / "capability-v1.json"), load_capability(FX / "capability-v2.json"))


def find(ch, kind, path):
    return [c for c in ch if c.kind == kind and path in (c.v1_path, c.v2_path)]


def test_planted_differences():
    ch = diff()
    assert find(ch, REMOVED, "Patient.nickname")
    assert find(ch, ADDED, "Patient.mrn")
    assert find(ch, CHANGED, "Patient.active")             # cardinality
    assert "cardinality 0..1 -> 1..1" in find(ch, CHANGED, "Patient.active")[0].detail
    assert "type CodeableConcept -> string" in find(ch, CHANGED, "Patient.maritalStatus")[0].detail


def test_rename_is_always_a_human_check():
    r = find(diff(), POSSIBLE_RENAME, "Patient.phoneNumber")[0]
    assert r.v2_path == "Patient.phone" and r.needs_human_check


def test_search_params_are_compared():
    ch = diff()
    assert find(ch, REMOVED, "Patient?legacy-id")
    assert not find(ch, REMOVED, "Patient?_id")

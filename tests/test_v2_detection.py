"""Part A features on SYNTHETIC fixtures: value sets, rules, official renames, context traps, unverifiable, severity."""
import pytest
from truthlayer.drift import (CRITICAL, EXAMPLE, GHOST, HIGH, LOW, MEDIUM, MISSING, UNVERIFIABLE, WRONG,
                              fix_first, write_reports)
from truthlayer.fhir_adapter import (Element, apply_profiles, load_definitions, load_maps, load_profile_overlay)
from truthlayer.maps import parse_version_map
from truthlayer.specdiff import (CHANGED, RENAMED, POSSIBLE_RENAME, diff_elements, rule_diffs)
from conftest import FX


def get(analysis, label, element):
    return [f for f in analysis.findings if f.label == label and element in (f.v1_element, f.v2_element)]


# ---- A2 rule changes
def test_value_set_and_binding_strength_change(analysis):
    f = get(analysis, WRONG, "Patient.gender")[0]
    assert {"value_set", "binding_strength"} <= set(f.sub_kinds)
    assert f.severity == HIGH
    assert "gender-b" in f.detail


def test_reference_target_change(analysis):
    f = get(analysis, WRONG, "Patient.managingOrganization")[0]
    assert "target_type" in f.sub_kinds and f.severity == HIGH


def test_profile_rules_slicing_must_support_required_slice(analysis):
    f = get(analysis, MISSING, "Patient.identifier")[0]
    assert {"slicing", "must_support"} <= set(f.sub_kinds)
    assert "required slices: mrn" in f.v2_def
    assert f.severity == MEDIUM


def test_rule_diffs_unit():
    a = Element("X.y", ("code",), 0, "1", binding="http://a/vs|1", strength="required", fixed="fixedCode=1")
    b = Element("X.y", ("code",), 1, "1", binding="http://a/vs|2", strength="required", fixed="fixedCode=2", must_support=True)
    kinds, _ = rule_diffs(a, b)
    assert {"cardinality", "now_required", "value_set_version", "fixed_default", "must_support"} <= set(kinds)
    assert "value_set" not in kinds      # same value set, only the version differs


def test_apply_profiles_overlay():
    base = load_definitions(sorted((FX / "defs-v2").glob("patient.json")))
    merged = apply_profiles(base, load_profile_overlay(sorted((FX / "profiles-v2").glob("*.json"))))
    assert merged["Patient.name"].must_support and not base["Patient.name"].must_support
    assert "required slices: mrn" in merged["Patient.identifier"].slicing


# ---- A3 children
def test_new_parent_lists_children(analysis):
    f = get(analysis, MISSING, "Coverage.class")[0]
    assert f.children_count == 2
    assert set(f.children) == {"Coverage.class.type", "Coverage.class.value"}
    assert f.severity == MEDIUM            # a child is required in v2
    assert "2 child" in f.plain_english


# ---- A4 context
def test_bare_resource_word_does_not_match_an_element(analysis):
    # the booklet says "Fetch the `Coverage` resource": Patient.coverage must NOT be flagged
    assert not [f for f in analysis.findings if f.v1_element == "Patient.coverage"]
    assert not [m for m in analysis.mentions if m.token == "Coverage" and m.category == "element"]


def test_prose_name_needs_its_resource_nearby(cfg, tmp_path):
    from truthlayer.docmap import Index, find_mentions, parse_markdown
    v1 = load_definitions(sorted((FX / "defs-v1").glob("*.json")))
    idx = Index(v1, {}, set())
    far = tmp_path / "far.md"
    far.write_text("# Notes\n\nThe dob value is shown to staff.\n")
    near = tmp_path / "near.md"
    near.write_text("# Notes\n\nThe patient record shows `dob` to staff.\n")
    assert not find_mentions(parse_markdown(far, "far.md"), idx, {"far.md": "Notes"})
    ms = find_mentions(parse_markdown(near, "near.md"), idx, {"near.md": "Notes"})
    assert ms and ms[0].evidence == "named_in_context"


# ---- A5 renames
def test_official_map_rename_vs_guess(analysis):
    dob = get(analysis, WRONG, "Patient.dob")[0]
    assert dob.change_kind == RENAMED and dob.severity == CRITICAL
    assert "official" in dob.plain_english
    guess = get(analysis, WRONG, "Patient.phoneNumber")[0]
    assert guess.change_kind == POSSIBLE_RENAME and guess.ask_human


def test_version_map_parser():
    m = parse_version_map(FX / "maps" / "Patient-version-maps.html")
    assert m == {"Patient.dob": "Patient.dateOfBirth"}
    assert load_maps([FX / "maps" / "missing.html"]) == {}


def test_without_map_the_same_pair_is_only_a_guess():
    v1 = load_definitions(sorted((FX / "defs-v1").glob("patient.json")))
    v2 = load_definitions(sorted((FX / "defs-v2").glob("patient.json")))
    ch = diff_elements(v1, v2, {})
    assert not [c for c in ch if c.kind == RENAMED]


# ---- A6 unverifiable
def test_unverifiable_header_and_policy(analysis):
    u = [f for f in analysis.findings if f.label == UNVERIFIABLE]
    subjects = {f.v1_element for f in u}
    assert "X-Member-Mode" in subjects and "token lifetime" in subjects
    hdr = next(f for f in u if f.v1_element == "X-Member-Mode")
    assert hdr.severity == MEDIUM and hdr.ask_human and hdr.locations[0]["line"] > 30
    assert fix_first(analysis.findings) and all(f.label != UNVERIFIABLE for f in fix_first(analysis.findings))


# ---- A1 severity and report
def test_severity_rules(analysis):
    sev = {(f.label, f.v1_element or f.v2_element): f.severity for f in analysis.findings}
    assert sev[(WRONG, "Patient.active")] == CRITICAL          # now required
    assert sev[(GHOST, "Patient.nickname")] == CRITICAL        # removed, named in text
    assert sev[(GHOST, "ReferralRequest")] == CRITICAL         # ghost resource
    assert sev[(EXAMPLE, "Patient.maritalStatus")] == HIGH     # wrong example
    assert sev[(MISSING, "Patient.mrn")] == MEDIUM             # required, never mentioned
    assert sev[(MISSING, "Patient.preferredLanguage")] == LOW  # optional addition


def test_report_has_fix_first_and_low_appendix(analysis, cfg):
    md, _ = write_reports(analysis, cfg)
    text = md.read_text()
    assert text.index("## In plain English") < text.index("## Fix these first") < text.index("## WRONG")
    assert "## Appendix: LOW items by resource" in text and "### Patient" in text
    first = text.split("## Fix these first")[1].split("\n## ")[0]
    assert "preferredLanguage" not in first
    assert text.count("1. **") <= 15
    assert "## UNVERIFIABLE" in text


def test_fix_first_is_capped_and_sorted(analysis):
    ff = fix_first(analysis.findings, limit=3)
    assert len(ff) == 3 and ff[0].severity == CRITICAL


# ---- robustness
def test_invalid_json_gives_clear_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    with pytest.raises(ValueError, match="not valid JSON"):
        load_definitions([bad])
    with pytest.raises(FileNotFoundError, match="not found"):
        load_definitions([tmp_path / "nope.json"])
    notsd = tmp_path / "x.json"
    notsd.write_text('{"resourceType": "Patient"}')
    with pytest.raises(ValueError, match="not a FHIR StructureDefinition"):
        load_definitions([notsd])

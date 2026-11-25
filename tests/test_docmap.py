from truthlayer.docmap import Index, find_mentions, json_keys, parse_markdown
from truthlayer.fhir_adapter import load_definitions
from conftest import FX


def blocks():
    return parse_markdown(FX / "docs-v1" / "patient-guide.md", "patient-guide.md")


def test_blocks_have_locations_and_kinds():
    bl = blocks()
    kinds = {b.kind for b in bl}
    assert {"prose", "table", "sample"} <= kinds
    sample = next(b for b in bl if b.kind == "sample")
    assert sample.section == "Patient guide > Sample" and sample.line > 20
    assert any(b.kind == "table" and "birthDate" in b.text for b in bl)


def test_json_keys_track_paths():
    keys = json_keys('{\n "resourceType": "Patient",\n "name": [\n {\n "family": "X"\n }\n ]\n}')
    assert ("family", ["name", "family"]) in [(k, p) for _, k, p, _ in keys]
    assert all(root == "Patient" for *_, root in keys)


def test_mentions_found():
    v1 = load_definitions(sorted((FX / "defs-v1").glob("*.json")))
    idx = Index(v1, {"Patient": {"legacy-id"}}, {"ReferralRequest"})
    ms = find_mentions(blocks(), idx, {"patient-guide.md": "Patient guide"})
    toks = {(m.token, m.kind) for m in ms}
    assert ("phoneNumber", "prose") in toks
    assert ("active", "table") in toks
    assert ("maritalStatus", "sample") in toks
    assert ("legacy-id", "prose") in toks and ("ReferralRequest", "prose") in toks

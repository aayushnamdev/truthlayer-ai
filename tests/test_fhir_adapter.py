from truthlayer.fhir_adapter import load_capability, load_definitions, load_types
from conftest import FX


def test_definitions_have_type_and_cardinality():
    v1 = load_definitions(sorted((FX / "defs-v1").glob("*.json")))
    e = v1["Patient.active"]
    assert (e.min, e.max, e.types) == (0, "1", ("boolean",))
    assert v1["Patient.name"].max == "*"
    assert "Patient" not in v1                      # the root itself is not an element


def test_capability_lists_resources_and_search_params():
    c = load_capability(FX / "capability-v1.json")
    assert set(c.resources) == {"Patient", "Coverage"}
    assert "legacy-id" in c.resources["Patient"]["search"]
    assert c.resources["Coverage"]["interactions"] == {"read"}


def test_missing_files_are_empty():
    assert load_capability(None).resources == {}
    assert load_types(None) == set()

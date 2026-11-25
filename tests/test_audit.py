from truthlayer import audit


def test_log_appends_lines(tmp_path):
    f = tmp_path / "a" / "log.jsonl"
    audit.log(f, "check", item="x")
    audit.log(f, "approval", item="P-1", approver="auto", model="m", prompt_hash="h")
    recs = audit.read(f)
    assert [r["action"] for r in recs] == ["check", "approval"]
    assert recs[1]["approver"] == "auto" and recs[1]["prompt_hash"] == "h" and "time" in recs[1]


def test_hashes(tmp_path):
    p = tmp_path / "f.txt"
    p.write_text("abc")
    assert audit.sha256_file(p) == audit.sha256_text("abc")

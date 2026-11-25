import pytest

from truthlayer import approval, fixer, publisher
from truthlayer.drift import write_reports
from truthlayer.mcp_server import Store, build_server


@pytest.fixture
def store(analysis, cfg):
    write_reports(analysis, cfg)
    fixer.propose_fixes(analysis, cfg)
    approval.auto_approve_high(cfg)
    publisher.publish(analysis, cfg, approval.load(cfg))
    return Store(cfg.publish_dir, cfg.reports_dir)


def test_search_and_get_page(store):
    hits = store.search_docs("phoneNumber nickname", "2")
    assert hits and "overview" in hits[0]["id"]
    assert "api_version" in store.get_page(hits[0]["id"])
    assert store.search_docs("zzzzqqq") == []


def test_drift_report_and_change(store):
    assert store.get_drift_report()["summary"]["findings"] > 0
    ch = store.get_change("Patient.mrn")
    assert ch["spec_changes"] and ch["findings"]


def test_cannot_read_outside_served_folders(store):
    with pytest.raises(ValueError):
        store.get_page("../../fixes/proposals")
    with pytest.raises(ValueError):
        store._safe(store.publish, "../audit/audit-log.jsonl")


def test_server_exposes_four_tools(cfg, store):
    import asyncio
    srv = build_server(cfg.publish_dir, cfg.reports_dir)
    tools = asyncio.run(srv.list_tools())
    names = {t.name for t in (tools.tools if hasattr(tools, "tools") else tools)}
    assert names == {"search_docs", "get_page", "get_drift_report", "get_change"}

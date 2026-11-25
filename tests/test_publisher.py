from docx import Document

from truthlayer import approval, fixer, publisher


def run(analysis, cfg, approve_all_high=True):
    fixer.propose_fixes(analysis, cfg)
    if approve_all_high:
        approval.auto_approve_high(cfg)
    return publisher.publish(analysis, cfg, approval.load(cfg))


def test_unapproved_fixes_are_not_published(analysis, cfg):
    m = run(analysis, cfg, approve_all_high=False)
    text = "".join(p.read_text() for p in (cfg.publish_dir / "pages").glob("*.md"))
    assert "(v2 note:" not in text and "removed in v2" not in text
    assert sum(p["fixes_applied"] for p in m["pages"]) == 0


def test_approved_fix_is_applied_and_page_has_front_matter(analysis, cfg):
    m = run(analysis, cfg)
    assert sum(p["fixes_applied"] for p in m["pages"]) >= 1
    page = next(p for p in (cfg.publish_dir / "pages").glob("*.md") if "overview" in p.name)
    t = page.read_text()
    for key in ("api_version:", "verified_on:", "sha256:", "truthlayer_version:", "status:"):
        assert key in t
    assert "removed in v2" in t or "v2 note" in t or "phone" in t


def test_pages_with_open_findings_are_flagged(analysis, cfg):
    run(analysis, cfg)
    t = next(p for p in (cfg.publish_dir / "pages").glob("*overview*.md")).read_text()
    assert "Not fully verified" in t and 'status: "needs_review"' in t


def test_llms_files_and_docx(analysis, cfg):
    m = run(analysis, cfg)
    assert "## Pages" in (cfg.publish_dir / "llms.txt").read_text()
    full = (cfg.publish_dir / "llms-full.txt").read_text()
    assert "Patient guide" in full or "Overview" in full
    d = Document(cfg.publish_dir / "export.docx")
    assert len(d.tables) == 1 and len(d.tables[0].rows) == len(m["pages"]) + 1
    assert any("Overview" in p.text for p in d.paragraphs)

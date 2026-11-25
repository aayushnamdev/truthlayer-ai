"""TruthLayer AI web dashboard (Streamlit). Start with:  truthlayer app   (or: make app)

Safety: nothing here calls the AI on page load. The AI runs only when the user presses
"Ask AI for a fix", and always inside the cost limit from truthlayer.yml.
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import streamlit as st

from truthlayer import approval, audit, dashboard_data as dd, fixer, pipeline, publisher
from truthlayer.budget import Budget, BudgetExceeded
from truthlayer.config import Config
from truthlayer.drift import analyse, write_reports
from truthlayer.settings import load_settings


def _root() -> Path:
    if "--root" in sys.argv:
        return Path(sys.argv[sys.argv.index("--root") + 1])
    return Path(os.environ.get("TRUTHLAYER_ROOT", "."))


st.set_page_config(page_title="TruthLayer AI", page_icon="✔", layout="wide")
st.markdown("""
<style>
  .block-container {padding-top: 2rem; max-width: 1250px;}
  h1, h2, h3 {letter-spacing: -0.01em;}
  .tl-card {border: 1px solid #e4e7ec; border-radius: 12px; padding: 14px 16px; background: #ffffff;}
  .tl-card .n {font-size: 28px; font-weight: 650; line-height: 1.1;}
  .tl-card .l {font-size: 12px; color: #667085; text-transform: uppercase; letter-spacing: .04em;}
  .tl-pill {display:inline-block; padding: 2px 9px; border-radius: 999px; font-size: 12px; color:#fff; font-weight: 600;}
  .tl-box {border: 1px solid #e4e7ec; border-radius: 10px; padding: 12px 14px; background:#f9fafb; font-size: 14px; white-space: pre-wrap;
           font-family: ui-monospace, SFMono-Regular, Menlo, monospace;}
  .tl-banner {border-radius: 10px; padding: 10px 14px; font-size: 14px;}
</style>
""", unsafe_allow_html=True)

ROOT = _root()
SETTINGS = load_settings(ROOT)


def pill(text: str, color: str) -> str:
    return f'<span class="tl-pill" style="background:{color}">{text}</span>'


def card(label: str, value: Any, col: Any, color: str = "#101828") -> None:
    col.markdown(f'<div class="tl-card"><div class="l">{label}</div><div class="n" style="color:{color}">{value}</div></div>',
                 unsafe_allow_html=True)


def active_cfg() -> Config:
    if "cfg" in st.session_state:
        return st.session_state["cfg"]
    return Config.real(ROOT)


def load_state() -> dict[str, Any]:
    cfg = active_cfg()
    rep = dd.load_report(cfg.reports_dir)
    score = None
    sp = cfg.reports_dir / "score.json"
    if sp.exists():
        score = json.loads(sp.read_text())
    info: dict[str, Any] = {}
    ip = cfg.reports_dir / "run-info.json"
    if ip.exists():
        info = json.loads(ip.read_text())
    props = None
    pp = cfg.fixes_dir / "proposals.json"
    if pp.exists():
        props = json.loads(pp.read_text())
    cost = None
    lp = cfg.fixes_dir / "cost-ledger.json"
    if lp.exists():
        cost = json.loads(lp.read_text())
    return {"cfg": cfg, "report": rep, "score": score, "info": info, "props": props, "ledger": cost}


def run_check(cfg: Config) -> None:
    t0 = time.perf_counter()
    a, sf = pipeline.check(cfg)
    secs = round(time.perf_counter() - t0, 2)
    cfg.reports_dir.mkdir(parents=True, exist_ok=True)
    (cfg.reports_dir / "run-info.json").write_text(json.dumps({"seconds": secs}))
    st.session_state["analysis_seconds"] = secs


# ---------------------------------------------------------------- sidebar
S = load_state()
cfg = S["cfg"]
with st.sidebar:
    st.markdown("### TruthLayer AI")
    st.caption("Verify docs after an API changes.")
    page = st.radio("Go to", ["Home", "Overview", "Fix these first", "Finding detail", "Downloads", "Audit log"],
                    label_visibility="collapsed")
    st.divider()
    if fixer.has_key():
        st.markdown('<div class="tl-banner" style="background:#ecfdf3;color:#067647">AI key found. Live AI runs only when you press a button, within the cost limit.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="tl-banner" style="background:#fffaeb;color:#b54708"><b>MOCK mode.</b> No ANTHROPIC_API_KEY is set, so fixes come from a simple built-in stand-in, not the AI.</div>', unsafe_allow_html=True)
    led = S["ledger"]
    spent = led["spent_usd"] if led else 0.0
    st.caption(f"AI budget: ${spent:.4f} of ${SETTINGS.ai.cost_limit_usd:.2f} used · model {SETTINGS.ai.model}")

report = S["report"]

# ---------------------------------------------------------------- pages
if page == "Home":
    st.title("TruthLayer AI")
    st.write("Checks whether API documentation is still true after the API changes, fixes only what broke, and republishes verified docs.")
    choice = st.radio("What do you want to check?", ["The bundled Blue Button case (v1 booklet vs FHIR R4)", "Upload my own specs and docs"])
    if choice.startswith("The bundled"):
        st.info("Uses the real CMS Blue Button v1 booklet, the STU3 and R4 definitions and the capability statements that come with this project.")
        if st.button("Run check", type="primary"):
            st.session_state.pop("cfg", None)
            with st.spinner("Comparing v1 and v2 …"):
                try:
                    run_check(Config.real(ROOT))
                    st.success("Done. Open Overview.")
                except (FileNotFoundError, ValueError) as exc:
                    st.error(f"Could not run the check: {exc}")
    else:
        c1, c2 = st.columns(2)
        up_v1 = c1.file_uploader("v1 definitions (StructureDefinition JSON, snapshot form)", type="json", accept_multiple_files=True)
        up_v2 = c2.file_uploader("v2 definitions (StructureDefinition JSON, snapshot form)", type="json", accept_multiple_files=True)
        up_c1 = c1.file_uploader("v1 capability statement (optional)", type="json")
        up_c2 = c2.file_uploader("v2 capability statement (optional)", type="json")
        up_docs = st.file_uploader("Docs folder: Markdown files", type="md", accept_multiple_files=True)
        if st.button("Run check on my files", type="primary"):
            if not (up_v1 and up_v2 and up_docs):
                st.error("Please add at least one v1 definition, one v2 definition and one Markdown doc.")
            else:
                tmp = Path(tempfile.mkdtemp(prefix="truthlayer-"))
                for sub in ("d1", "d2", "docs"):
                    (tmp / sub).mkdir()
                def save(files: list[Any], sub: str) -> list[Path]:
                    out = []
                    for f in files:
                        p = tmp / sub / Path(f.name).name
                        p.write_bytes(f.getvalue()); out.append(p)
                    return out
                c = Config(root=tmp, defs_v1=save(up_v1, "d1"), defs_v2=save(up_v2, "d2"), docs_dir=tmp / "docs",
                           reports_dir=tmp / "reports", fixes_dir=tmp / "fixes", publish_dir=tmp / "publish",
                           audit_file=tmp / "audit/audit-log.jsonl")
                save(up_docs, "docs")
                if up_c1:
                    c.cap_v1 = save([up_c1], "d1")[0]
                if up_c2:
                    c.cap_v2 = save([up_c2], "d2")[0]
                try:
                    run_check(c)
                    st.session_state["cfg"] = c
                    st.success("Done. Open Overview.")
                except (FileNotFoundError, ValueError) as exc:
                    st.error(f"Could not run the check: {exc}")
    if report:
        st.caption(f"Latest report: {report['summary']['findings']} findings.")

elif report is None:
    st.title("No report yet")
    st.info("Go to Home and press Run check. (Nothing runs until you press a button.)")

elif page == "Overview":
    st.title("Overview")
    secs = S["info"].get("seconds") or st.session_state.get("analysis_seconds")
    cost = (S["props"] or {}).get("meta", {}).get("estimated_cost_usd") if S["props"] else None
    cards = dd.score_cards(report, S["score"], secs, cost)
    cols = st.columns(4)
    for col, sev in zip(cols, dd.SEVERITIES):
        card(f"{sev.title()} findings", cards["by_severity"][sev], col, dd.SEV_COLOR[sev])
    st.write("")
    c = st.columns(4)
    card("CMS recall", cards["cms_recall"] + (f" ({cards['cms_recall_pct']}%)" if cards["cms_recall_pct"] is not None else ""), c[0])
    card("Real drift found", cards["real_drift_found"], c[1])
    card("Run time", f"{cards['run_seconds']} s" if cards["run_seconds"] is not None else "n/a", c[2])
    card("AI cost", f"${cards['ai_cost_usd']:.4f}" if cards["ai_cost_usd"] is not None else "$0.0000 (no AI run)", c[3])
    st.write("")
    st.markdown((cfg.reports_dir / "drift-report.md").read_text().split("## Fix these first")[0])

elif page == "Fix these first":
    st.title("Fix these first")
    c1, c2, c3 = st.columns([2, 2, 3])
    sevs = c1.multiselect("Severity", dd.SEVERITIES, default=["CRITICAL", "HIGH"])
    labs = c2.multiselect("Label", dd.LABELS)
    q = c3.text_input("Search element or text")
    rows = dd.filter_findings(report["findings"], sevs, labs, q)
    st.caption(f"{len(rows)} findings")
    st.dataframe([{"ID": f["id"], "Severity": f["severity"], "Label": f["label"], "Confidence": f["confidence"],
                   "Element": f["v1_element"] or f["v2_element"],
                   "Where": (f["locations"][0]["file"] + ":" + str(f["locations"][0]["line"])) if f["locations"] else "-",
                   "What": f["plain_english"]} for f in rows], use_container_width=True, hide_index=True)

elif page == "Finding detail":
    st.title("Finding detail")
    fs = dd.filter_findings(report["findings"], dd.SEVERITIES[:3], None, "")
    ids = [f["id"] for f in fs] or [f["id"] for f in report["findings"]]
    fid = st.selectbox("Finding", ids, format_func=lambda i: next((f"{i} · {f['severity']} · {f['label']} · {f['v1_element'] or f['v2_element']}" for f in report["findings"] if f["id"] == i), i))
    f = next(x for x in report["findings"] if x["id"] == fid)
    st.markdown(pill(f["severity"], dd.SEV_COLOR[f["severity"]]) + " " + pill(f["label"], "#344054") + " " +
                pill(("ask a human" if f["confidence"] == "LOW" else "high confidence"), "#667085"), unsafe_allow_html=True)
    st.write(f["plain_english"])
    st.caption(f"Why this severity: {f.get('why_severity', '')}. Confidence: {f['why_confidence']}")
    left, right = st.columns(2)
    with left:
        st.subheader("Old booklet says")
        if f["locations"]:
            text, lo = dd.booklet_context(cfg.root if cfg.root != Path('.') else ROOT, f["locations"][0])
            st.markdown(f'<div class="tl-box">{dd.highlight_tokens(text, [l["token"] for l in f["locations"]])}</div>', unsafe_allow_html=True)
            st.caption(f"{f['locations'][0]['file']} from line {lo}")
        else:
            st.markdown('<div class="tl-box">The booklet never mentions this.</div>', unsafe_allow_html=True)
    with right:
        st.subheader("v2 truth")
        a_html, b_html = dd.mark_diff(f["v1_def"] or "(not in v1)", f["v2_def"] or "(not in v2)")
        st.markdown(f'<div class="tl-box"><b>v1:</b> {a_html}\n\n<b>v2:</b> {b_html}</div>', unsafe_allow_html=True)
        if f.get("children"):
            st.caption(f"{f['children_count']} child element(s): " + ", ".join(c.split(".")[-1] for c in f["children"][:12]))
    st.divider()
    st.subheader("AI fix")
    props = (S["props"] or {}).get("proposals", [])
    prop = next((p for p in props if p["finding_id"] == fid), None)
    if f["severity"] in SETTINGS.ai.fix_severities and f["locations"] and f["label"] in ("WRONG", "GHOST", "EXAMPLE"):
        label = "Ask AI for a fix" if fixer.has_key() else "Make a MOCK fix (no AI key set)"
        if st.button(label):
            try:
                from truthlayer.drift import Analysis  # noqa: F401
                a = analyse(cfg)
                fixer.propose_one(a, cfg, SETTINGS, fid, live=fixer.has_key())
                st.rerun()
            except (BudgetExceeded, fixer.AIUnavailable, ValueError, KeyError) as exc:
                st.error(fixer.scrub(str(exc)))
    else:
        st.caption("Only CRITICAL/HIGH wrong, ghost or example findings are sent to the fixer.")
    if prop:
        o_html, n_html = dd.mark_diff(prop["original"], prop["proposed"])
        b1, b2 = st.columns(2)
        b1.markdown(f'<div class="tl-box">{o_html}</div>', unsafe_allow_html=True)
        b2.markdown(f'<div class="tl-box">{n_html}</div>', unsafe_allow_html=True)
        st.caption(f"{prop['id']} · {prop['mode']} · status {prop['status']} · {prop['reason']}")
        a1, a2, _ = st.columns([1, 1, 4])
        if a1.button("Approve", type="primary", key=f"ap{prop['id']}"):
            approval.set_status(cfg, prop["id"], "APPROVED", "dashboard-user"); st.rerun()
        if a2.button("Reject", key=f"rj{prop['id']}"):
            approval.set_status(cfg, prop["id"], "REJECTED", "dashboard-user"); st.rerun()

elif page == "Downloads":
    st.title("Downloads")
    st.write("Build the verified docs first. Only approved fixes are applied; no AI is used.")
    if st.button("Build verified docs", type="primary"):
        try:
            a = analyse(cfg)
            props = approval.load(cfg) if (cfg.fixes_dir / "proposals.json").exists() else None
            publisher.publish(a, cfg, props)
            st.success("Built.")
        except (FileNotFoundError, ValueError) as exc:
            st.error(str(exc))
    pd_ = cfg.publish_dir
    if (pd_ / "manifest.json").exists():
        st.download_button("Verified Markdown (zip)", dd.zip_pages(pd_), "truthlayer-pages.zip")
        for name, mime in (("llms.txt", "text/plain"), ("llms-full.txt", "text/plain")):
            if (pd_ / name).exists():
                st.download_button(name, (pd_ / name).read_bytes(), name, mime)
        if (pd_ / "export.docx").exists():
            st.download_button("Word export", (pd_ / "export.docx").read_bytes(), "export.docx")
    if cfg.audit_file.exists():
        st.download_button("Audit log (JSON lines)", cfg.audit_file.read_bytes(), "audit-log.jsonl")

elif page == "Audit log":
    st.title("Audit log")
    rows = dd.read_audit(cfg.audit_file)
    acts = sorted({r["action"] for r in rows})
    sel = st.selectbox("Action", ["(all)"] + acts)
    rows = [r for r in rows if sel == "(all)" or r["action"] == sel]
    st.dataframe(rows, use_container_width=True, hide_index=True)

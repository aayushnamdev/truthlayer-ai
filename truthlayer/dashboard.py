"""TruthLayer AI web dashboard (Streamlit). Start with:  truthlayer app   (or: streamlit run streamlit_app.py)

Two modes:
  * Saved real run (default, read-only): shows the stored results of the real Blue Button run from files in the repo.
    It never writes anything and never calls the AI, so a public copy can not spend money.
  * Work on my own project: run checks, approve fixes, and (only if an API key exists) press "Ask AI for a fix".
Nothing calls the AI on page load. An optional APP_PASSWORD secret puts a password in front of everything.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

import streamlit as st

from truthlayer import approval, fixer, pipeline, publisher
from truthlayer import dashboard_data as dd
from truthlayer.budget import BudgetExceeded
from truthlayer.config import Config
from truthlayer.drift import analyse
from truthlayer.settings import SettingsError, load_settings


def _root() -> Path:
    if "--root" in sys.argv:
        return Path(sys.argv[sys.argv.index("--root") + 1])
    return Path(os.environ.get("TRUTHLAYER_ROOT", "."))


st.set_page_config(page_title="TruthLayer AI", page_icon="✔", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
  .block-container {padding-top: 1.6rem; max-width: 1250px;}
  h1, h2, h3 {letter-spacing: -0.01em;}
  .tl-card {border: 1px solid #e4e7ec; border-radius: 12px; padding: 14px 16px; background: #ffffff; margin-bottom: 8px;}
  .tl-card .n {font-size: 28px; font-weight: 650; line-height: 1.1;}
  .tl-card .l {font-size: 12px; color: #667085; text-transform: uppercase; letter-spacing: .04em;}
  .tl-pill {display:inline-block; padding: 2px 9px; border-radius: 999px; font-size: 12px; color:#fff; font-weight: 600; margin-right: 4px;}
  .tl-box {border: 1px solid #e4e7ec; border-radius: 10px; padding: 12px 14px; background:#f9fafb; font-size: 14px; white-space: pre-wrap;
           overflow-wrap: anywhere; font-family: ui-monospace, SFMono-Regular, Menlo, monospace;}
  .tl-banner {border-radius: 10px; padding: 10px 14px; font-size: 14px; margin-bottom: 10px;}
  @media (max-width: 640px) {
    .block-container {padding: 1rem 0.8rem 3rem 0.8rem;}
    h1 {font-size: 1.6rem !important;}
    .tl-card .n {font-size: 22px;}
    .tl-box {font-size: 12.5px; padding: 10px;}
    div[data-testid="stHorizontalBlock"] {gap: 0.5rem;}
  }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------- optional password gate (before anything is shown)
_pw = dd.password_required(st.secrets)
if _pw and not st.session_state.get("auth_ok"):
    st.title("TruthLayer AI")
    entered = st.text_input("Password", type="password")
    if entered and dd.password_ok(entered, _pw):
        st.session_state["auth_ok"] = True
        st.rerun()
    elif entered:
        st.error("Wrong password.")
    st.stop()

ROOT = _root()
try:
    SETTINGS = load_settings(ROOT)
except SettingsError as exc:
    st.error(f"Settings problem: {exc}")
    st.stop()

SAVED = "Saved real run (read-only)"
WORK = "Work on my own project"


def pill(text: str, color: str) -> str:
    return f'<span class="tl-pill" style="background:{color}">{text}</span>'


def card(label: str, value: Any, col: Any, color: str = "#101828") -> None:
    col.markdown(f'<div class="tl-card"><div class="l">{label}</div><div class="n" style="color:{color}">{value}</div></div>',
                 unsafe_allow_html=True)


def read_json(p: Path) -> Any:
    try:
        return json.loads(p.read_text()) if p.exists() else None
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------- sidebar: mode and status
with st.sidebar:
    st.markdown("### TruthLayer AI")
    source = st.radio("Data", [SAVED, WORK], key="source")
    read_only = source == SAVED
    if read_only:
        st.caption("Shows the stored results of the real Blue Button run. Nothing is changed and no AI is called.")
    if fixer.has_key() and not read_only:
        st.markdown('<div class="tl-banner" style="background:#ecfdf3;color:#067647">AI key found. The AI runs only when you press a button, inside the cost limit.</div>', unsafe_allow_html=True)
    elif not fixer.has_key():
        st.markdown('<div class="tl-banner" style="background:#fffaeb;color:#b54708"><b>No AI key.</b> The AI button is hidden. Fixes shown here were made earlier (real AI or MOCK, each is labelled).</div>', unsafe_allow_html=True)

if read_only or "cfg" not in st.session_state:
    cfg = Config.real(ROOT)
else:
    cfg = st.session_state["cfg"]

report = dd.load_report(cfg.reports_dir)
score = read_json(cfg.reports_dir / "score.json")
info = read_json(cfg.reports_dir / "run-info.json") or {}
props_data = read_json(cfg.fixes_dir / "proposals.json")
ledger = read_json(cfg.fixes_dir / "cost-ledger.json")
ai_use = dd.ledger_summary(ledger, SETTINGS.ai.price_in_per_mtok, SETTINGS.ai.price_out_per_mtok)

# ---------------------------------------------------------------- top navigation (works on a phone)
PAGES = ["Home", "Overview", "Fix these first", "Finding detail", "Downloads", "Audit log"]
st.title("TruthLayer AI")
page = st.radio("Page", PAGES, horizontal=True, label_visibility="collapsed", key="nav")


def about_panel() -> None:
    sp = dd.SCORE_HISTORY
    with st.expander("About this demo", expanded=(page == "Home")):
        st.markdown(f"""
**What you are looking at.** A real check of the CMS **Blue Button 2.0** Medicare API as it moved from v1 (FHIR STU3) to v2 (FHIR R4).

- **Real data.** CMS's public API definitions, the CMS Blue Button and CARIN profiles, and HL7's official R3-to-R4 maps.
- **The old booklet.** The v1 documentation CMS removed from its website, recovered from CMS's public GitHub history (a **2023** snapshot).
- **CMS's own change list.** 35 v1-to-v2 changes that CMS explicitly states. They are the answer key.
- **Honest scoring.** The first score ({sp[0]['caught']} of {sp[0]['of']}) was taken **blind**: the tool was built without looking at the answer key. The later scores ({sp[1]['caught']} of {sp[1]['of']}) came **after improving the tool on the known misses**, so they show gaps being closed, not an independent test.
- **AI cost so far.** {ai_use['calls']} real AI calls (claude-haiku-5-5), {ai_use['input_tokens']:,} + {ai_use['output_tokens']:,} tokens, about **${ai_use['cost_usd']:.2f}** at assumed prices.
- Detection is plain, repeatable code. AI is only used to write fixes, and nothing is published without approval.
""")


# ---------------------------------------------------------------- pages
if page == "Home":
    st.write("Checks whether API documentation is still true after the API changes, fixes only what broke, and republishes verified docs.")
    about_panel()
    if read_only:
        if report:
            s = report["summary"]
            st.success(f"Saved real run loaded: {s['findings']} findings. Open **Overview** or **Fix these first**.")
        else:
            st.warning("No saved run found in this copy of the project.")
    else:
        choice = st.radio("What do you want to check?", ["The bundled Blue Button case", "Upload my own specs and docs"])
        if choice.startswith("The bundled"):
            if st.button("Run check", type="primary"):
                st.session_state.pop("cfg", None)
                with st.spinner("Comparing v1 and v2 …"):
                    try:
                        pipeline.check(Config.real(ROOT))
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
                            p.write_bytes(f.getvalue())
                            out.append(p)
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
                        pipeline.check(c)
                        st.session_state["cfg"] = c
                        st.success("Done. Open Overview.")
                    except (FileNotFoundError, ValueError) as exc:
                        st.error(f"Could not run the check: {exc}")

elif report is None:
    st.info("No report yet. Go to Home" + ("." if read_only else " and press Run check. (Nothing runs until you press a button.)"))

elif page == "Overview":
    cards = dd.score_cards(report, score, info.get("seconds"), ai_use["cost_usd"])
    cols = st.columns(4)
    for col, sev in zip(cols, dd.SEVERITIES):
        card(f"{sev.title()} findings", cards["by_severity"][sev], col, dd.SEV_COLOR[sev])
    row2 = st.columns(4)
    card("CMS recall", cards["cms_recall"] + (f" ({cards['cms_recall_pct']}%)" if cards["cms_recall_pct"] is not None else ""), row2[0])
    card("Real drift found", cards["real_drift_found"], row2[1])
    card("Run time", f"{cards['run_seconds']} s" if cards["run_seconds"] is not None else "n/a", row2[2])
    card("AI cost so far", f"${ai_use['cost_usd']:.2f} · {ai_use['calls']} calls", row2[3])
    st.subheader("Three scores against CMS's 35 changes")
    st.dataframe([{"Score": h["name"], "Caught": f"{h['caught']} of {h['of']}", "Blind": "yes" if h["blind"] else "no",
                   "What changed": h["note"]} for h in dd.SCORE_HISTORY], use_container_width=True, hide_index=True)
    about_panel()
    md = (cfg.reports_dir / "drift-report.md").read_text() if (cfg.reports_dir / "drift-report.md").exists() else ""
    st.markdown(md.split("## Fix these first")[0])

elif page == "Fix these first":
    c1, c2 = st.columns(2)
    sevs = c1.multiselect("Severity", dd.SEVERITIES, default=["CRITICAL", "HIGH"])
    labs = c2.multiselect("Label", dd.LABELS)
    q = st.text_input("Search element or text")
    rows = dd.filter_findings(report["findings"], sevs, labs, q)
    st.caption(f"{len(rows)} findings")
    st.dataframe([{"ID": f["id"], "Severity": f["severity"], "Label": f["label"], "Confidence": f["confidence"],
                   "Element": f["v1_element"] or f["v2_element"],
                   "Where": (f["locations"][0]["file"] + ":" + str(f["locations"][0]["line"])) if f["locations"] else "-",
                   "What": f["plain_english"]} for f in rows], use_container_width=True, hide_index=True)

elif page == "Finding detail":
    fs = dd.filter_findings(report["findings"], dd.SEVERITIES[:2], None, "") or dd.filter_findings(report["findings"])
    ids = [f["id"] for f in fs]
    all_findings: list[dict[str, Any]] = report["findings"]
    fid = str(st.selectbox("Finding", ids, format_func=lambda i: next((f"{i} · {x['severity']} · {x['label']} · {x['v1_element'] or x['v2_element']}"
                                                                        for x in all_findings if x["id"] == i), i)))
    f = next(x for x in all_findings if x["id"] == fid)
    st.markdown(pill(f["severity"], dd.SEV_COLOR[f["severity"]]) + pill(f["label"], "#344054") +
                pill("ask a human" if f["confidence"] == "LOW" else "high confidence", "#667085"), unsafe_allow_html=True)
    st.write(f["plain_english"])
    st.caption(f"Why this severity: {f.get('why_severity', '')}. Confidence: {f['why_confidence']}")
    left, right = st.columns(2)
    with left:
        st.subheader("Old booklet says")
        if f["locations"]:
            text, lo = dd.booklet_context(ROOT, f["locations"][0])
            st.markdown(f'<div class="tl-box">{dd.highlight_tokens(text, [loc["token"] for loc in f["locations"]])}</div>', unsafe_allow_html=True)
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
    st.subheader("Fix")
    props = (props_data or {}).get("proposals", [])
    prop = next((p for p in props if p["finding_id"] == fid), None)
    can_ask = (not read_only) and fixer.has_key() and f["severity"] in SETTINGS.ai.fix_severities and f["locations"] \
        and f["label"] in ("WRONG", "GHOST", "EXAMPLE")
    if can_ask and st.button("Ask AI for a fix"):                     # the only place the AI can be called, and only here
        try:
            fixer.propose_one(analyse(cfg), cfg, SETTINGS, fid, live=True)
            st.rerun()
        except (BudgetExceeded, fixer.AIUnavailable, ValueError, KeyError) as exc:
            st.error(fixer.scrub(str(exc)))
    if prop:
        o_html, n_html = dd.mark_diff(prop["original"], prop["proposed"])
        st.markdown(f'<div class="tl-box"><b>Before</b>\n{o_html}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="tl-box" style="margin-top:8px"><b>After</b>\n{n_html}</div>', unsafe_allow_html=True)
        label = "real AI (claude-haiku-5-5)" if prop["mode"] == "LIVE" else "MOCK stand-in, not AI"
        st.caption(f"{prop['id']} · {label} · status {prop['status']} · {prop['reason']}")
        if not read_only:
            a1, a2 = st.columns(2)
            if a1.button("Approve", type="primary", key=f"ap{prop['id']}"):
                approval.set_status(cfg, prop["id"], "APPROVED", "dashboard-user")
                st.rerun()
            if a2.button("Reject", key=f"rj{prop['id']}"):
                approval.set_status(cfg, prop["id"], "REJECTED", "dashboard-user")
                st.rerun()
    elif not can_ask:
        st.caption("No fix was proposed for this finding. Only CRITICAL/HIGH wrong, ghost or example findings are sent to the fixer.")

elif page == "Downloads":
    if not read_only:
        st.write("Build the verified docs first. Only approved fixes are applied; no AI is used.")
        if st.button("Build verified docs", type="primary"):
            try:
                props_now = approval.load(cfg) if (cfg.fixes_dir / "proposals.json").exists() else None
                publisher.publish(analyse(cfg), cfg, props_now)
                st.success("Built.")
            except (FileNotFoundError, ValueError) as exc:
                st.error(str(exc))
    pd_ = cfg.publish_dir
    if (pd_ / "manifest.json").exists():
        st.download_button("Verified Markdown (zip)", dd.zip_pages(pd_), "truthlayer-pages.zip")
        for name in ("llms.txt", "llms-full.txt"):
            if (pd_ / name).exists():
                st.download_button(name, (pd_ / name).read_bytes(), name, "text/plain")
        if (pd_ / "export.docx").exists():
            st.download_button("Word export", (pd_ / "export.docx").read_bytes(), "export.docx")
        for sample in sorted((pd_ / "samples").glob("*.json")) if (pd_ / "samples").exists() else []:
            st.download_button(f"Corrected sample: {sample.name}", sample.read_bytes(), sample.name, "application/json")
    else:
        st.info("Nothing published yet.")
    if cfg.audit_file.exists():
        st.download_button("Audit log (JSON lines)", cfg.audit_file.read_bytes(), "audit-log.jsonl")

elif page == "Audit log":
    rows = dd.read_audit(cfg.audit_file)
    acts = sorted({r["action"] for r in rows})
    sel = st.selectbox("Action", ["(all)", *acts])
    rows = [r for r in rows if sel == "(all)" or r["action"] == sel]
    st.caption(f"{len(rows)} entries (newest first, up to 500)")
    st.dataframe(rows, use_container_width=True, hide_index=True)


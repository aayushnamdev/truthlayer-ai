"""The `truthlayer` command line."""
from __future__ import annotations

import functools
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import click

from . import __version__, approval, fixer, logging_setup, pipeline, publisher
from .budget import BudgetExceeded
from .config import Config
from .drift import SEVERITY_RANK
from .settings import SettingsError, load_dotenv, load_settings

SEV_CHOICES = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"]


def friendly(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Turn expected problems (missing/invalid files, bad settings, budget) into one clear line, exit code 2."""
    @functools.wraps(fn)
    def wrapper(*a: Any, **k: Any) -> Any:
        try:
            return fn(*a, **k)
        except (FileNotFoundError, ValueError, SettingsError, KeyError, BudgetExceeded, fixer.AIUnavailable) as exc:
            click.echo(f"Error: {fixer.scrub(str(exc.args[0] if isinstance(exc, KeyError) else exc))}", err=True)
            sys.exit(2)
    return wrapper


@click.group()
@click.version_option(__version__)
@click.option("--root", default=".", help="Project folder (default: current folder).", type=click.Path())
@click.option("--log-json", is_flag=True, help="Write logs as JSON lines.")
@click.option("--log-level", default="WARNING", help="DEBUG, INFO, WARNING, ERROR.")
@click.pass_context
def main(ctx: click.Context, root: str, log_json: bool, log_level: str) -> None:
    """TruthLayer AI: check API docs for drift, fix only what broke, republish verified docs."""
    logging_setup.setup(log_json, log_level)
    load_dotenv(root)
    ctx.obj = {"root": root}


def _cfg(ctx: click.Context) -> Config:
    return Config.real(ctx.obj["root"])


@main.command()
@click.option("--fail-on", type=click.Choice(SEV_CHOICES), default=None,
              help="Exit 1 if any finding at or above this severity exists (default: from truthlayer.yml).")
@click.pass_context
@friendly
def check(ctx: click.Context, fail_on: str | None) -> None:
    """Find drift and style problems. Writes reports/drift-report.md and .json."""
    cfg = _cfg(ctx)
    st = load_settings(cfg.root)
    a, sf = pipeline.check(cfg)
    c = Counter(f.label for f in a.findings)
    sv = Counter(f.severity for f in a.findings)
    click.echo(f"{len(a.findings)} findings by label {dict(c)}; by severity {dict(sv)}; {len(sf)} style findings. "
               f"See {cfg.reports_dir}/drift-report.md")
    level = fail_on or st.fail_on_severity
    if level != "NONE":
        worst = [f for f in a.findings if SEVERITY_RANK[f.severity] <= SEVERITY_RANK[level] and f.label != "UNVERIFIABLE"]
        if worst:
            click.echo(f"FAIL: {len(worst)} finding(s) at {level} or worse.", err=True)
            sys.exit(1)


@main.command()
@click.pass_context
@friendly
def style(ctx: click.Context) -> None:
    """Run only the client style rules."""
    from . import style as st
    cfg = _cfg(ctx)
    if not cfg.style_rules or not cfg.style_rules.exists():
        raise FileNotFoundError(f"style rules file not found: {cfg.style_rules}")
    res = st.check_docs(cfg.docs_dir, cfg.style_rules, cfg.root)
    for r in res:
        click.echo(f"{r['rule']} {r['file']}:{r['line']}  {r['suggestion']}  [{r['snippet']}]")
    click.echo(f"{len(res)} style findings")


@main.command()
@click.option("--live", is_flag=True, help="Really call the AI (needs ANTHROPIC_API_KEY). Without it: MOCK mode.")
@click.option("--max-calls", type=int, default=None, help="Extra cap on AI calls for this run.")
@click.pass_context
@friendly
def fix(ctx: click.Context, live: bool, max_calls: int | None) -> None:
    """Make fix proposals (PENDING). MOCK mode unless --live. Stays inside the cost limit in truthlayer.yml."""
    cfg = _cfg(ctx)
    a, _ = pipeline.check(cfg)
    data = fixer.propose_fixes(a, cfg, live=live, limit_calls=max_calls)
    m = data["meta"]
    click.echo(f"Mode: {m['mode']}. {len(data['proposals'])} proposals saved to {cfg.fixes_dir}/proposals.json "
               f"(calls {m['calls_this_run']}, tokens in/out {m['input_tokens']}/{m['output_tokens']}, "
               f"est. ${m['estimated_cost_usd']}; budget left ${m['budget']['remaining_usd']}). All PENDING.")
    if m["stopped"]:
        click.echo(f"Note: {m['stopped']}")
    if live and m["mode"] == "MOCK":
        click.echo("ANTHROPIC_API_KEY is not set, so this ran in MOCK mode.", err=True)


@main.command("ai-test")
@click.pass_context
@friendly
def ai_test(ctx: click.Context) -> None:
    """Make ONE real AI call and show its real token use (counts toward the budget)."""
    cfg = _cfg(ctx)
    st = load_settings(cfg.root)
    if not fixer.has_key():
        raise ValueError("ANTHROPIC_API_KEY is not set")
    a, _ = pipeline.check(cfg)
    r = fixer.ai_test(a, cfg, st)
    click.echo(json.dumps({k: v for k, v in r.items() if k != "revised"}, indent=1))


@main.command()
@click.option("--pending", is_flag=True, help="Show only proposals not yet decided.")
@click.pass_context
@friendly
def review(ctx: click.Context, pending: bool) -> None:
    """Show the proposed fixes with before/after."""
    click.echo(approval.review_text(_cfg(ctx), pending))


@main.command()
@click.argument("proposal_id", required=False)
@click.option("--auto-approve-high", is_flag=True, help="Approve every HIGH-confidence proposal; approver is recorded as 'auto'.")
@click.option("--by", default="human", help="Name recorded in the audit log.")
@click.pass_context
@friendly
def approve(ctx: click.Context, proposal_id: str | None, auto_approve_high: bool, by: str) -> None:
    """Approve a proposal by ID, or all HIGH-confidence ones with --auto-approve-high."""
    cfg = _cfg(ctx)
    if auto_approve_high:
        ids = approval.auto_approve_high(cfg)
        click.echo(f"Auto-approved {len(ids)} HIGH-confidence proposals: {', '.join(ids) or 'none'}")
    elif proposal_id:
        approval.set_status(cfg, proposal_id, "APPROVED", by)
        click.echo(f"{proposal_id} APPROVED by {by}")
    else:
        raise click.UsageError("Give a proposal ID or --auto-approve-high")


@main.command()
@click.argument("proposal_id")
@click.option("--by", default="human")
@click.pass_context
@friendly
def reject(ctx: click.Context, proposal_id: str, by: str) -> None:
    """Reject a proposal by ID."""
    approval.set_status(_cfg(ctx), proposal_id, "REJECTED", by)
    click.echo(f"{proposal_id} REJECTED by {by}")


@main.command()
@click.pass_context
@friendly
def publish(ctx: click.Context) -> None:
    """Publish verified pages (only APPROVED fixes are applied) to publish/."""
    cfg = _cfg(ctx)
    a, _ = pipeline.check(cfg)
    props = approval.load(cfg) if (cfg.fixes_dir / "proposals.json").exists() else None
    m = publisher.publish(a, cfg, props)
    click.echo(f"Published {len(m['pages'])} pages to {cfg.publish_dir}/ (llms.txt, llms-full.txt, export.docx)")


@main.command()
@click.option("--auto-approve-high", is_flag=True)
@click.option("--live", is_flag=True, help="Really call the AI (within the cost limit).")
@click.pass_context
@friendly
def run(ctx: click.Context, auto_approve_high: bool, live: bool) -> None:
    """Whole pipeline: check, fix, (auto-)approve, publish. Prints wall-clock time."""
    r = pipeline.run_all(_cfg(ctx), auto_approve_high, live)
    click.echo(f"Done in {r['seconds']}s. {len(r['analysis'].findings)} findings, "
               f"{len(r['proposals']['proposals'])} proposals, {len(r['auto_approved'])} auto-approved, "
               f"{len(r['manifest']['pages'])} pages published (mode {r['proposals']['meta']['mode']}).")


@main.command()
@click.option("--out", default="demo-output", help="Where to write the demo results.")
@friendly
def demo(out: str) -> None:
    """Run everything on the SYNTHETIC test fixtures (no real data, no AI key needed)."""
    fx = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
    if not fx.is_dir():
        raise FileNotFoundError("tests/fixtures not found: run the demo from a source checkout")
    out_p = Path(out)
    if out_p.exists():
        shutil.rmtree(out_p)
    cfg = Config.fixtures(fx, out_p)
    cfg.root = fx.parent.parent
    r = pipeline.run_all(cfg, auto_high=True)
    c = Counter(f.label for f in r["analysis"].findings)
    click.echo("SYNTHETIC DEMO (fixtures, not CMS data)")
    click.echo(f"  findings by label: {dict(c)}")
    click.echo(f"  by severity: {dict(Counter(f.severity for f in r['analysis'].findings))}")
    click.echo(f"  proposals: {len(r['proposals']['proposals'])} (mode {r['proposals']['meta']['mode']}), auto-approved: {len(r['auto_approved'])}")
    click.echo(f"  pages published: {len(r['manifest']['pages'])} -> {cfg.publish_dir}")
    click.echo(f"  style findings: {len(r['style'])}")


@main.command("serve-mcp")
@click.pass_context
@friendly
def serve_mcp(ctx: click.Context) -> None:
    """Start the MCP server (stdio) serving publish/ and reports/."""
    from .mcp_server import build_server
    cfg = _cfg(ctx)
    build_server(cfg.publish_dir, cfg.reports_dir).run()


@main.command()
@click.option("--port", default=8501, type=int)
@click.pass_context
@friendly
def app(ctx: click.Context, port: int) -> None:
    """Start the web dashboard (Streamlit)."""
    import subprocess
    script = Path(__file__).resolve().parent / "dashboard.py"
    sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", str(script), "--server.port", str(port),
                              "--", "--root", str(Path(ctx.obj["root"]).resolve())]))


@main.command()
@click.argument("truth_csv", type=click.Path())
@click.pass_context
@friendly
def score(ctx: click.Context, truth_csv: str) -> None:
    """Score reports/drift-report.json against a ground-truth CSV. Use only AFTER tuning is finished."""
    from .score import score as sc
    cfg = _cfg(ctx)
    if not Path(truth_csv).exists():
        raise FileNotFoundError(f"ground-truth file not found: {truth_csv}")
    r = sc(Path(truth_csv), cfg.reports_dir / "drift-report.json")
    (cfg.reports_dir / "score.json").write_text(json.dumps(r, indent=1))
    click.echo(f"caught {r['caught']}/{r['n']}, spec-diff-only {r['spec_diff_only']}, missed {r['missed']}; "
               f"precision {r['precision']:.2f} ({r['findings_matched']}/{r['findings_total']})")

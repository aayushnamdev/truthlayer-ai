"""The `truthlayer` command line."""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path
import click
from . import __version__, approval, audit, fixer, pipeline, publisher
from .config import Config


def _cfg(root: str) -> Config:
    return Config.real(root)


@click.group()
@click.version_option(__version__)
@click.option("--root", default=".", help="Project folder (default: current folder).", type=click.Path())
@click.pass_context
def main(ctx, root):
    """TruthLayer AI: check API docs for drift, fix only what broke, republish verified docs."""
    ctx.obj = _cfg(root)


@main.command()
@click.pass_obj
def check(cfg):
    """Find drift and style problems. Writes reports/drift-report.md and .json."""
    a, sf = pipeline.check(cfg)
    from collections import Counter
    c = Counter(f.label for f in a.findings)
    click.echo(f"{len(a.findings)} findings: {dict(c)}; {len(sf)} style findings. See {cfg.reports_dir}/drift-report.md")


@main.command()
@click.pass_obj
def style(cfg):
    """Run only the client style rules."""
    from . import style as st
    res = st.check_docs(cfg.docs_dir, cfg.style_rules, cfg.root)
    for r in res:
        click.echo(f"{r['rule']} {r['file']}:{r['line']}  {r['suggestion']}  [{r['snippet']}]")
    click.echo(f"{len(res)} style findings")


@main.command()
@click.pass_obj
def fix(cfg):
    """Ask the AI (or MOCK mode if no ANTHROPIC_API_KEY) for fixes. Saves fixes/proposals.json as PENDING."""
    a, _ = pipeline.check(cfg)
    data = fixer.propose_fixes(a, cfg)
    m = data["meta"]
    click.echo(f"Mode: {m['mode']}. {len(data['proposals'])} proposals saved to {cfg.fixes_dir}/proposals.json "
               f"(tokens in/out {m['input_tokens']}/{m['output_tokens']}, est. ${m['estimated_cost_usd']}). All PENDING.")


@main.command()
@click.option("--pending", is_flag=True, help="Show only proposals not yet decided.")
@click.pass_obj
def review(cfg, pending):
    """Show the proposed fixes with before/after."""
    click.echo(approval.review_text(cfg, pending))


@main.command()
@click.argument("proposal_id", required=False)
@click.option("--auto-approve-high", is_flag=True, help="Approve every HIGH-confidence proposal; approver is recorded as 'auto'.")
@click.option("--by", default="human", help="Name recorded in the audit log.")
@click.pass_obj
def approve(cfg, proposal_id, auto_approve_high, by):
    """Approve a proposal by ID, or all HIGH-confidence ones with --auto-approve-high."""
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
@click.pass_obj
def reject(cfg, proposal_id, by):
    """Reject a proposal by ID."""
    approval.set_status(cfg, proposal_id, "REJECTED", by)
    click.echo(f"{proposal_id} REJECTED by {by}")


@main.command()
@click.pass_obj
def publish(cfg):
    """Publish verified pages (only APPROVED fixes are applied) to publish/."""
    a, _ = pipeline.check(cfg)
    props = approval.load(cfg) if (cfg.fixes_dir / "proposals.json").exists() else None
    m = publisher.publish(a, cfg, props)
    click.echo(f"Published {len(m['pages'])} pages to {cfg.publish_dir}/ (llms.txt, llms-full.txt, export.docx)")


@main.command()
@click.option("--auto-approve-high", is_flag=True)
@click.pass_obj
def run(cfg, auto_approve_high):
    """Whole pipeline: check, fix, (auto-)approve, publish. Prints wall-clock time."""
    r = pipeline.run_all(cfg, auto_approve_high)
    click.echo(f"Done in {r['seconds']}s. {len(r['analysis'].findings)} findings, "
               f"{len(r['proposals']['proposals'])} proposals, {len(r['auto_approved'])} auto-approved, "
               f"{len(r['manifest']['pages'])} pages published.")


@main.command()
@click.option("--out", default="demo-output", help="Where to write the demo results.")
def demo(out):
    """Run everything on the SYNTHETIC test fixtures (no real data, no AI key needed)."""
    fx = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    cfg = Config.fixtures(fx, out)
    cfg.root = fx.parent.parent  # so doc paths print relative to the repo
    r = pipeline.run_all(cfg, auto_high=True)
    from collections import Counter
    c = Counter(f.label for f in r["analysis"].findings)
    click.echo("SYNTHETIC DEMO (fixtures, not CMS data)")
    click.echo(f"  findings by label: {dict(c)}")
    click.echo(f"  proposals: {len(r['proposals']['proposals'])} (mode {r['proposals']['meta']['mode']}), auto-approved: {len(r['auto_approved'])}")
    click.echo(f"  pages published: {len(r['manifest']['pages'])} -> {cfg.publish_dir}")
    click.echo(f"  style findings: {len(r['style'])}")


@main.command("serve-mcp")
@click.pass_obj
def serve_mcp(cfg):
    """Start the MCP server (stdio) serving publish/ and reports/."""
    from .mcp_server import build_server
    build_server(cfg.publish_dir, cfg.reports_dir).run()


@main.command()
@click.argument("truth_csv", type=click.Path(exists=True))
@click.pass_obj
def score(cfg, truth_csv):
    """Score reports/drift-report.json against a ground-truth CSV. Use only AFTER tuning is finished."""
    from .score import score as sc
    r = sc(Path(truth_csv), cfg.reports_dir / "drift-report.json")
    (cfg.reports_dir / "score.json").write_text(json.dumps(r, indent=1))
    click.echo(f"caught {r['caught']}/{r['n']}, spec-diff-only {r['spec_diff_only']}, missed {r['missed']}; "
               f"precision {r['precision']:.2f} ({r['findings_matched']}/{r['findings_total']})")

# TruthLayer AI

TruthLayer AI checks whether API documentation is still true after an API changes, fixes only the parts that broke, and republishes a verified copy that people and AI assistants can read.

Test case: the CMS **Blue Button 2.0** Medicare API, moving from **v1 (FHIR STU3)** to **v2 (FHIR R4)**. The "booklet" being checked is the old v1 documentation CMS removed from its website (recovered from CMS's public GitHub history, see `truth/SOURCES.md`).

## What it does, in plain English
1. **Compares the two API versions** using the official FHIR definitions and each server's capability statement.
2. **Reads the old booklet** and finds every place it names a field, search option or resource.
3. **Labels each problem:**
   - **WRONG**: the text names something that still exists but changed (or was probably renamed).
   - **GHOST**: the text describes something that is gone in v2.
   - **EXAMPLE**: only a sample shows the old name.
   - **MISSING**: v2 adds or changes something the booklet never mentions.
   Each one is HIGH confidence, or LOW ("ask a human").
4. **Checks house style** (rules in `rules/healthplan-style.yml`; these are **SYNTHETIC**, invented for a pretend health plan).
5. **Proposes fixes** with AI, giving the AI only the one passage and the matching v2 definition.
6. **Waits for approval.** Nothing is published unless a fix is APPROVED.
7. **Publishes** one Markdown page per section, `llms.txt`, `llms-full.txt` and a Word file, and can serve them to Claude through an MCP server.
8. **Logs everything** (checks, findings, proposals, approvals, publishes) to `audit/audit-log.jsonl`.

All the detection is plain, repeatable code. AI is used **only** to write the fixes.

## Install
Needs Python 3.11 or newer.
```bash
pip install -e ".[test]"
```

## Commands
Run from the project folder (or pass `--root PATH`).

| Command | What it does |
|---|---|
| `truthlayer check` | Find drift and style problems. Writes `reports/drift-report.md` (plain English first) and `.json`. |
| `truthlayer style` | Run only the style rules. |
| `truthlayer fix` | Make fix proposals into `fixes/proposals.json`, all PENDING. Uses the AI if `ANTHROPIC_API_KEY` is set, otherwise **MOCK mode** (clearly labelled, no AI). Model: env `TRUTHLAYER_MODEL` (default `claude-haiku-5-5`). Tokens and estimated cost are saved. |
| `truthlayer review [--pending]` | Show proposals with before/after. |
| `truthlayer approve ID` | Approve one proposal (`--by NAME` to record who). |
| `truthlayer approve --auto-approve-high` | Approve every HIGH-confidence proposal that really changes something. Recorded as approver `auto`. |
| `truthlayer reject ID` | Reject a proposal. |
| `truthlayer publish` | Write `publish/` (pages, `llms.txt`, `llms-full.txt`, `export.docx`). Only APPROVED fixes are applied. |
| `truthlayer run [--auto-approve-high]` | check + fix + approve + publish in one go, with timing. |
| `truthlayer demo` | Run everything on the SYNTHETIC test fixtures. No real data or AI key needed. |
| `truthlayer serve-mcp` | Start the MCP server (see below). |
| `truthlayer score truth/v1-v2-changes.csv` | Compare findings with a ground-truth list. Use only after tuning is finished (see the honesty rule). |

The cost figure uses **assumed** prices (`TRUTHLAYER_PRICE_IN_PER_MTOK` / `TRUTHLAYER_PRICE_OUT_PER_MTOK`, default 1 and 5 dollars per million tokens). Set them to your real rates.

## The honesty rule
The detection logic is built and tuned **only** from the v1/v2 definitions, the docs and the synthetic fixtures. The list of CMS's own v1-to-v2 changes (`truth/v1-v2-changes.csv`) is opened only at the scoring step, and the first score is reported unchanged. If the tool is improved afterwards, the new score is reported separately with exactly what changed. See `reports/results.md`.

## Connect the MCP server to Claude
The server only reads `publish/` and `reports/`. Tools: `search_docs(query, api_version)`, `get_page(id)`, `get_drift_report()`, `get_change(element)`.

First run `truthlayer run --auto-approve-high` so those folders exist. Then add it to Claude Code:
```bash
claude mcp add truthlayer -- truthlayer --root /full/path/to/truthlayer-ai serve-mcp
```
For Claude Desktop, add this to `claude_desktop_config.json`:
```json
{ "mcpServers": { "truthlayer": { "command": "truthlayer", "args": ["--root", "/full/path/to/truthlayer-ai", "serve-mcp"] } } }
```

## Tests
```bash
pytest
```
Test data is invented and lives in `tests/fixtures/`, marked SYNTHETIC.

## Known limits
See "What this does not show" and the missed-change table in `reports/results.md`. In short: value-set bindings, profile slicing and HTTP headers are not compared; renames are guesses that always need a human; MISSING findings are numerous and mostly low value.

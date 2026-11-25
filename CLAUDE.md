# TruthLayer AI

TruthLayer AI is a **verification tool**. It checks whether API documentation is still
accurate after an API changes, fixes only what broke, and republishes verified,
AI-readable docs.

Real test case: the **CMS Blue Button 2.0 Medicare API**, moving from **v1 (FHIR STU3)** to
**v2 (FHIR R4)**.

## Current phase
Phases 1-5 are done (collect data, recover v1 docs, tool + first score in `reports/results.md`). **Branch `v1-production`** adds severity, rule/profile checks, a dashboard, CI and a second score in `reports/results-v2.md`. The real-AI fixer has run 37 calls in total (about $0.07); see `reports/results-v2.md` and `results-v3.md`. Go-live work: sample edits, saved-run dashboard, `streamlit_app.py`.

## Folder structure
| Path | Contents |
|---|---|
| `data/v1/`, `data/v2/` | Machine-readable API descriptions (FHIR capability statements) |
| `data/` | Other machine-readable files (e.g. Postman collection, if obtainable) |
| `docs/v1/`, `docs/v2/` | Public CMS documentation saved as Markdown (the "booklet" to be checked) |
| `truth/` | Ground truth: `v1-v2-changes.csv`, `SOURCES.md`, `PHASE1-REPORT.md`, `sources/` (raw copies of CMS source docs) |
| `rules/` | Client style rules (SYNTHETIC) |
| `data/fhir-defs/` | Official HL7 StructureDefinitions (STU3, R4) for Patient, Coverage, EOB, plus resource-name lists |
| `truthlayer/` | The Python package (CLI `truthlayer`) |
| `tests/`, `tests/fixtures/` | pytest tests; invented SYNTHETIC fixtures |
| `reports/`, `fixes/`, `publish/`, `audit/` | Outputs: drift report + results, fix proposals, published docs, audit log |

## Rules
1. Use only public CMS material. Never invent data.
2. Every saved file must be listed in `truth/SOURCES.md` with its URL, fetch date and SHA256 hash.
3. Anything we write ourselves (not from CMS) must be marked **SYNTHETIC**.
4. Ground truth lists only changes CMS explicitly states; do not infer changes.

## Architecture (package `truthlayer`)
`fhir_adapter` (read definitions + capability) -> `specdiff` (ADDED/REMOVED/CHANGED/POSSIBLE_RENAME, search params) ->
`docmap` (parse booklet into located blocks, find element mentions) -> `drift` (WRONG/EXAMPLE/MISSING/GHOST + HIGH/LOW, reports) ->
`style` (rule engine) -> `fixer` (AI only here; MOCK mode without key) -> `approval` (nothing publishes unless APPROVED) ->
`publisher` (pages, llms files, docx) -> `mcp_server` (serves publish/ and reports/ only). `audit` logs every step; `pipeline` glues; `cli` is the command line; `score` is used only at the scoring step.
New in 1.0: `settings` (truthlayer.yml), `budget` (hard cost limit ledger), `maps` (HL7 R3-R4 renames), `unverifiable`, `dashboard` + `dashboard_data` (Streamlit), `logging_setup`.

## Commands
`truthlayer check [--fail-on S] | style | fix [--live] | ai-test | review | approve [ID | --auto-approve-high] | reject ID | publish | run [--live] | app | demo | serve-mcp | score CSV`. Make: `make install | test | run | app | demo`. Tests: `pytest`, `ruff check .`, `mypy`.

## Extra rules for Phases 3-5
5. Detection is deterministic code. AI is used only in `fixer`.
6. **Honesty rule:** do not read `truth/v1-v2-changes.csv` while building or tuning detection. Score once with `truthlayer score`, report that score unchanged, and report any later improvement separately with what changed.
7. Invented test data goes in `tests/fixtures/` and is marked SYNTHETIC.
8. **Budget rule for AI:** only claude-haiku-5-5, hard limit and call cap from `truthlayer.yml`, fix only CRITICAL/HIGH, never print/log/commit the API key. AI runs only with `--live` or a dashboard button.
9. Keep `reports/results.md` (first score) unchanged; new scores go to a new file with the list of changes.
10. Never run a MOCK `fix`/`run` over real AI proposals (the tool now refuses without `--overwrite`). Never write the API key to any file.

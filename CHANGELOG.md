# Changelog

## 1.1.0
- New label NEEDS_NOTE; WRONG now means the text states something false. Third score in `reports/results-v3.md`.
- `truthlayer fix --live --retry-unparseable`; `truthlayer app --host`; `requirements.txt`.

## 1.0.0 (branch `v1-production`)
### Detection
- Every finding has a severity (CRITICAL, HIGH, MEDIUM, LOW). The report opens with "Fix these first" (max 15); LOW items are in an appendix by resource.
- Rule changes are compared: value-set bindings and strength, fixed/default values, reference target types, slicing, required slices, must-support. Added CARIN Blue Button IG (R4) and CMS Blue Button IG (STU3) profiles, base differences kept apart from profile-only ones.
- New parents are grouped but their children are listed and counted.
- Context-aware matching: a booklet passage links to an element only with a path, a JSON path, a field list/table, or a lowerCamel name whose resource is named nearby.
- Renames use HL7's official R3-to-R4 maps first, name similarity second ("ask a human").
- New label UNVERIFIABLE for header and policy statements no spec can prove.
- Scorer counts the children a finding lists.
### AI fixer
- Hard cost limit ($1.00), call cap (25), haiku only, 400 output tokens, CRITICAL/HIGH only, retries with backoff counted in the budget, key scrubbed from all output.
- **Behaviour change:** the fixer now calls the AI only with `--live` (before, it did whenever a key was set). New `truthlayer ai-test`.
### Product
- Streamlit dashboard (`truthlayer app`), GitHub Action drift check, CI (pytest, ruff, mypy), Dockerfile, Makefile, `truthlayer.yml`, `.env.example`, pinned dependencies, structured logging, clear errors for missing or invalid files.
### Results
- Second score 32 of 35 (first: 21 of 35); see `reports/results-v2.md`. Real-AI fixer run once (25 calls, about $0.04).

## 0.1.0 (branch `phase-3-5`)
- First version: spec diff, docs map, drift labels, style checker, MOCK/AI fixer, approvals, publisher, MCP server, audit log, tests. First score 21 of 35.

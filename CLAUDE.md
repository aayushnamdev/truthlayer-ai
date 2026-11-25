# TruthLayer AI

TruthLayer AI is a **verification tool**. It checks whether API documentation is still
accurate after an API changes, fixes only what broke, and republishes verified,
AI-readable docs.

Real test case: the **CMS Blue Button 2.0 Medicare API**, moving from **v1 (FHIR STU3)** to
**v2 (FHIR R4)**.

## Current phase
**Phase 1 — "Gather the truth".** Only collect real, public data. Do not build the tool yet.

## Folder structure
| Path | Contents |
|---|---|
| `data/v1/`, `data/v2/` | Machine-readable API descriptions (FHIR capability statements) |
| `data/` | Other machine-readable files (e.g. Postman collection, if obtainable) |
| `docs/v1/`, `docs/v2/` | Public CMS documentation saved as Markdown (the "booklet" to be checked) |
| `truth/` | Ground truth: `v1-v2-changes.csv`, `SOURCES.md`, `PHASE1-REPORT.md`, `sources/` (raw copies of CMS source docs) |
| `rules/` | Client style rules (SYNTHETIC) |

## Rules
1. Use only public CMS material. Never invent data.
2. Every saved file must be listed in `truth/SOURCES.md` with its URL, fetch date and SHA256 hash.
3. Anything we write ourselves (not from CMS) must be marked **SYNTHETIC**.
4. Ground truth lists only changes CMS explicitly states; do not infer changes.

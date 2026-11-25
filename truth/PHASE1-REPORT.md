# Phase 1 report: Gather the truth

Date: 2026-11-25. Branch: `phase-1`. Everything here is public CMS material; our own files are marked.

## What was collected

| Area | Result |
|---|---|
| v1 capability statement | `data/v1/capability.json` — valid JSON, FHIR 3.0.2 (STU3), 3 resources |
| v2 capability statement | `data/v2/capability.json` — valid JSON, FHIR 4.0.1 (R4), 3 resources |
| Current docs (saved to `docs/v2/`) | 10 pages: `/api-documentation/` plus its 9 sub-pages (authorization, calling-the-api, consuming-the-data, developer-sandbox, explore-the-api, implementation-guides, optimizing-your-app, v3-faq, v3-migration-guide). `/developers` only redirects here. |
| v1 docs (`docs/v1/`) | 1 page: `/terms/v1/` (terms of service) |
| Also saved (`docs/v2/`) | `/terms/v2/` |
| Ground truth | `truth/v1-v2-changes.csv`, **35 changes** |
| Raw source copies | `truth/sources/` (BCDA page, 3 BFD RFCs, 2 BFD wiki pages) |
| Style rules (SYNTHETIC) | `rules/healthplan-style.yml`, 11 rules |
| Provenance | `truth/SOURCES.md` (URL, fetch date, SHA256 for every file) |

### Resource types in the capability statements
Both versions declare the same three resources, each with `read` and `search-type`:
- **Patient**, **Coverage**, **ExplanationOfBenefit**

No other resource types are listed.

Search parameters that differ (from the capability files themselves):
- Coverage: v2 adds `_profile`.
- Patient: v1 has `_has:Coverage`; v2 has `_has:Coverage.extension` and `_has:Coverage.rfrncyr`.

I did not add these to the ground truth, because CMS does not state them as v1-to-v2 changes. They are good candidates for Phase 2 checks.

## Ground truth: 35 changes

| change_type | count |
|---|---|
| changed | 18 |
| added | 9 |
| renamed | 5 |
| removed | 3 |

By resource: ExplanationOfBenefit 15, Coverage 12, Patient 8.

Sources:
- BCDA v1/v2 comparison page.
- BFD v2 RFCs for Patient and Coverage (status "Implemented").
- BFD wiki "Making Requests to BFD".

Rows with "example" evidence come from CMS lists that give only examples. For instance, CMS says "Fifteen fields" went optional to mandatory and "about 35" EOB elements were added, but it names only some of them. The CSV holds only the named ones, so it is a lower bound.

## What failed

1. **Postman collection**: HTTP 404 on both `bluebutton.cms.gov` and `api.bluebutton.cms.gov`. It is not in the CMSgov repos I cloned either. Not saved.
2. **`https://bluebutton.cms.gov/v1/`**: HTTP 404. The current site no longer serves a v1 docs section, so `docs/v1/` has only the v1 terms page.
3. **Blocked fetch**: I tried to pull archived copies of the v1 docs and the Postman file from the Internet Archive. The Bash tool refused that fetch, so I did not retry or work around it. If you want those, approve it or fetch them yourself.
4. **GitHub wiki web pages** are not reachable here, so I read the wiki from its git repo instead.

## Surprises

- **The current CMS docs are about v3, not v2.** The live `/api-documentation/` set includes a "v3 Migration Guide" and "v3 FAQ". The pages I saved to `docs/v2/` are "current docs" (mostly v2 era, with v3 material). They are not a clean v2-only booklet. Decide in Phase 2 which pages count as the v2 booklet.
- **CMS's own v1-to-v2 list is thin.** The BFD "Migrating to V2 FAQ" says "We are currently working on a detailed breakdown of the differences", and it points to the generic FHIR R3-to-R4 diff. The real detail is in the BCDA page and the RFCs.
- **CMS sources disagree on `Coverage.grouping`.** BCDA calls it "removed" (equivalent is `Coverage.class`). The BFD RFC lists it as both renamed and deleted. I recorded one row, `renamed`, citing the RFC.
- **The BFD RFC's Patient section says "Renamed Items: NONE"**, so there is no Patient rename in the ground truth.
- Both sandboxes report software "Blue Button API: Direct 2.288.0" and a current date, so the capability statements are live snapshots and will drift.
- `bluebutton.cms.gov` runs a different (Astro) site now. Old `/v1/` and the Postman asset have gone.
- The CMS sources are about BCDA/BFD in places. BCDA says it "is based on" its own implementation, so a few rows are BCDA statements about the shared BFD data model, not Blue Button 2.0 docs. Each row's `source_url` shows which.

## Not done (by design)
No tool code was written. `truth/v1-v2-changes.csv` and `rules/healthplan-style.yml` were written by us (the CSV is compiled from CMS statements; the rules are SYNTHETIC).

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
3. **Blocked fetch**: my first attempt to pull archived copies from the Internet Archive was refused by the Bash tool and not retried. The v1 docs were recovered from CMS GitHub instead (see "v1 docs recovery"). The Postman file is still missing.
4. **GitHub wiki web pages** are not reachable here, so I read the wiki from its git repo instead.

## Surprises

- **The current CMS docs are about v3, not v2.** The live `/api-documentation/` set includes a "v3 Migration Guide" and "v3 FAQ". The pages I saved to `docs/v2/` are "current docs" (mostly v2 era, with v3 material). They are not a clean v2-only booklet. Decide in Phase 2 which pages count as the v2 booklet.
- **CMS's own v1-to-v2 list is thin.** The BFD "Migrating to V2 FAQ" says "We are currently working on a detailed breakdown of the differences", and it points to the generic FHIR R3-to-R4 diff. The real detail is in the BCDA page and the RFCs.
- **CMS sources disagree on `Coverage.grouping`.** BCDA calls it "removed" (equivalent is `Coverage.class`). The BFD RFC lists it as both renamed and deleted. I recorded one row, `renamed`, citing the RFC.
- **The BFD RFC's Patient section says "Renamed Items: NONE"**, so there is no Patient rename in the ground truth.
- Both sandboxes report software "Blue Button API: Direct 2.288.0" and a current date, so the capability statements are live snapshots and will drift.
- `bluebutton.cms.gov` runs a different (Astro) site now. Old `/v1/` and the Postman asset have gone.
- Some sources are about BCDA, not Blue Button. BCDA is a separate CMS API that shares the underlying BFD (Beneficiary FHIR Data) server with Blue Button, so a few rows are BCDA statements about the shared data model, not Blue Button 2.0 docs. Each row's `source_url` shows which.

## Not done (by design)
No tool code was written. `truth/v1-v2-changes.csv` and `rules/healthplan-style.yml` were written by us (the CSV is compiled from CMS statements; the rules are SYNTHETIC).

## v1 docs recovery

**Where from:** CMS's own GitHub repo `CMSgov/bluebutton-site-static` (the old website source), not the Internet Archive. The v1 page was deleted from the repo in commit `f474e7c6` (2025-10-06) and unpublished in `eeb860d1` (2025-08-08). I took the snapshot at commit `f9391f119db329a9d308da8652e7be8a8c4a842a` (2023-12-26, when v1 and v2 were both live). The v1 page was last changed in `1491270c` (2023-03-27).

**Pages recovered: 2 pages, plus 2 samples.**
- `docs/v1/blue-button-v1-stu3-docs.md` ← `_pages/v1.md` (the old `/v1/` page, ~1,100 lines)
- `docs/v1/explanation-of-benefits-fhir.md` ← `_pages/eob.md` (the old `/eob/` page, linked from `/v1/`)
- `data/v1/sample-patient-entry.json`, `data/v1/sample-coverage-entry.json` (STU3 samples linked from `/v1/`)
- With the existing `docs/v1/terms-v1.md` (live terms page), `docs/v1/` has 3 pages.
- Not recovered: `/checklist/` and `/guide/` (production access). They never mention v1/STU3.
- Not saved: `sample-eob-entry.json`; CMS published it as invalid JSON.
- Caveat: these are the Markdown sources converted to GitHub Markdown, so a few HTML blocks (alert boxes, `<pre>` code samples) remain as HTML, and code sample indentation is flattened inside `<pre>` blocks.

**Which of the 35 ground truth changes the v1 docs mention** (text search of each `v1_element`, then reading the hits):
- **Named explicitly as v1 fields (6):** CHG-002 `careTeamLinkId`, CHG-003 `diagnosisLinkId`, CHG-004 `service`, CHG-008 `patient`, CHG-009 `referral`, CHG-015 `type`. All are in the EOB page's field lists.
- **Only appear in sample JSON, not described (3):** CHG-020 `gender` value, CHG-021 and CHG-022 `Patient.identifier` (the `hicnHash` identifier).
- **Not mentioned (26):** CHG-001, 005, 006, 007, 010, 016-019, 023-030, plus the 9 "added" rows (CHG-011-014, 031-035), which have no v1 element.
- Not-mentioned examples: `Coverage.grouping`, `Patient.animal`, `Eob.hospitalization`, the `IncludeIdentifiers` header and the cardinality changes.

**Read this as:** the v1 booklet covers only about 6 of the 35 changes by name. The rest are changes the v1 docs never talk about. A verifier checking v2 docs against this booklet will find most of its work in places where the old docs were silent.

# TruthLayer AI results, second score (branch `v1-production`)

`reports/results.md` (the first score) is unchanged. The first-run files are kept in `reports/first-run/`.

## Read this first: how fair is the second score?
- The first score was taken blind (see `results.md`). **This second score is not blind.** I changed the tool *after* seeing which of the 35 CMS changes it missed, and the first-score misses (value-set rules, slicing, children of new parents) are exactly what several changes target. Treat the improvement as "fixing known gaps", not as an independent test.
- Two of the changes were made after I had already seen a second-iteration score (29/35): the base-vs-profile split and counting children in the scorer. Both are listed below.
- **The AI fixer was run for real afterwards** (the key was supplied in chat after the first version of this file; see "Real AI run" at the bottom). The first part of this file (scores) comes from the MOCK run and is unaffected: detection never uses AI.

## First vs second score
| Measure | First score (`results.md`) | Second score |
|---|---|---|
| Findings in total | 65 | 155 |
| By label | WRONG 8, GHOST 1, EXAMPLE 5, MISSING 51 | WRONG 20, GHOST 1, EXAMPLE 12, MISSING 112, UNVERIFIABLE 10 |
| By severity | not available | CRITICAL 9, HIGH 22, MEDIUM 39, LOW 85 |
| CMS changes caught by a finding | 21 of 35 (60%) | **32 of 35 (91%)** |
| Seen in the v1/v2 difference list but no finding | 2 | 2 (`Eob.hospitalization`, `Patient.animal`: removed, never mentioned in the booklet) |
| Missed completely | 12 | **1** (`IncludeIdentifiers` header) |
| Catches that point at booklet text (WRONG or EXAMPLE) | 9 of 21 | 17 of 32 |
| Catches by MISSING only ("v2 has it, booklet silent") | 12 | 15 |
| Strict precision (finding is on CMS's list) | 43% (28 of 65) | 28% (43 of 155) |
| Precision of the CRITICAL + HIGH findings | n/a | 42% (13 of 31) |
| Run time (whole pipeline, wall clock) | 0.34 s | 0.63 s |
| AI tokens and cost | 0 / $0.00 (MOCK) | 15,458 in+out tokens, about $0.04 at assumed prices (real run, see bottom) |

Precision fell because the tool now looks at many more rules, so it reports many more real differences that CMS never listed (see below). It is not a sign that the extra findings are wrong.

## Every change made since the first score
1. **Rule changes (A2).** Besides type and cardinality, the tool now compares value-set bindings and their strength, fixed/default values and reference target types. Official files added to `data/fhir-defs/` and logged in `truth/SOURCES.md`: CARIN Blue Button IG 1.0.0 (R4) profiles for Patient, Coverage and EOB from packages.fhir.org, and CMS's own Blue Button STU3 IG profiles from `CMSgov/bluebutton-site-static`. Profile rules compared: slicing, required slices, must-support, stricter minimums.
2. **Base vs profile split (after the 29/35 iteration).** Base HL7 STU3 vs R4 differences are compared separately from differences only the profiles add (labelled `profile:`). Before this, the CMS Blue Button profile hid the base change `EOB.patient` optional to required.
3. **New parent elements (A3).** Children of a new or removed parent are still grouped under it, but each child is now listed and counted in the finding.
4. **Scorer counts children.** `truthlayer score` now treats a finding on a parent as covering the children it lists. This is a change to the scoring step, and it moved two rows (`Coverage.class.name`, `Coverage.class.value`) from missed to caught.
5. **Context-aware matching (A4).** A booklet passage is linked to an element only with a full dotted path, a JSON path, a field list/table under the right resource, or a lowerCamel name whose resource is named nearby. Capitalised resource words like "Coverage" never match an element. This removes the first-score false alarm `ExplanationOfBenefit.insurance.coverage`.
6. **Renames (A5).** HL7's official R3-to-R4 version maps (3 pages saved in `data/fhir-defs/maps/`) are parsed first: 7 confirmed renames (`RENAMED`). Name similarity is the fallback and stays "ask a human".
7. **UNVERIFIABLE (A6).** Statements about HTTP headers and policies, which no spec can prove, are listed separately with their booklet location (10 found).
8. **Severity (A1).** Every finding is CRITICAL, HIGH, MEDIUM or LOW, and the report opens with "Fix these first" (max 15) with LOW items in an appendix by resource.
9. **Fixer guard rails.** The AI fixer is only run with `--live`, only on CRITICAL/HIGH, at most 25 calls, claude-haiku-5-5 only, 400 output tokens, with a hard $1.00 limit checked before every attempt. Retries count toward the budget.

## Which CMS changes are still not fully caught
| CMS change | Status |
|---|---|
| `IncludeIdentifiers` header (CHG-023) | **Missed.** The booklet never mentions it, so there is nothing to compare. |
| `Eob.hospitalization` (CHG-006), `Patient.animal` (CHG-016) | In the difference list, no finding: removed, and the booklet is silent. |

## False alarms and extra findings
- 112 findings are not on CMS's list. I read all 39 that are CRITICAL, HIGH or MEDIUM. **None was a wrong match**: each is a real difference in the official definitions or profiles that CMS did not list (for example `ExplanationOfBenefit.insurance` 0..1 to 1..*, new value sets such as `claim-modifiers`, new search parameters `_has:Coverage.extension` and `_profile`).
- Several of those are low value: about 6 are only a must-support flag changing (`billablePeriod`, `Patient.birthDate`, `careTeam.sequence`). Treat them as noise, not as breakage.
- The other 73 (64 LOW missing and 9 LOW unverifiable policy sentences) were **not read one by one**; the missing ones come from the same mechanical comparison.
- One of the 39 is the MEDIUM UNVERIFIABLE `Content-Encoding` header sentence; it is a statement a person has to confirm, not an error.

## The "Fix these first" list (real run)
See `reports/drift-report.md`. Nine are CRITICAL and 22 HIGH; the report shows the first 15.

## Real AI run (claude-haiku-5-5)
- **Test call first:** 283 input and 212 output tokens (about $0.0013).
- **Full run:** 24 more calls, 8,644 input and 6,813 output tokens. **Total 25 calls, 8,927 in / 7,025 out, about $0.044 at the assumed prices ($0.088 as charged to the budget, which doubles prices). Budget left: $0.91 of $1.00.** It stopped at the 25-call cap. No failed or retried calls. Prices are my assumption, not looked up; check the Anthropic console for the real bill.
- **Results of the 24 proposals:** 2 changed the text, 15 correctly left it unchanged, 7 came back unparseable (the 400-token cap cut the JSON off because the model wrote a long "reason").
- **The model was right to decline most.** The booklet passages are bare field names like `insurance` or `status`. The change (for example 0..1 to 1..*) does not make any word in them wrong, so there was nothing to fix. This also says something about the detector: many "WRONG" findings are real spec changes where the old text never made a claim that is now false.
- **Fix after the run:** the prompt now asks for a reason of at most 20 words and to return unchanged text if nothing is wrong. Not re-run, because the 25-call limit is used up.

### Before/after examples
1. **Renamed field (approved automatically, HIGH confidence).** Old booklet, `explanation-of-benefits-fhir.md` line 108, listed `careTeamLinkId`. v2 calls it `careTeamSequence` (HL7's official map). Now says `careTeamSequence`.
2. **Same kind of rename.** Line 109, `diagnosisLinkId` became `diagnosisSequence`.
3. **Correctly left alone.** Line 95 says only `insurance`. v2 now requires at least one insurance entry, but the text states no count, so the model returned it unchanged, with the reason "it states no cardinality". That is a note for a writer to add the new rule, not a wording fix.

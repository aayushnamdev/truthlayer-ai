# TruthLayer AI results: v1 booklet vs v2, scored against CMS's own change list

Tool state scored: commit `8bd1681` (branch `phase-3-5`). **This is the first and only score; nothing was changed after it.**

## How honest is this score?
- Detection was built and tuned using only the v1/v2 StructureDefinitions, the two capability statements, the docs in `docs/v1/`, and the SYNTHETIC fixtures in `tests/fixtures/`.
- `truth/v1-v2-changes.csv` was **not opened by any build step**. It was read for the first time by `truthlayer score`.
- **Caveat you should know:** I wrote that CSV in an earlier Phase 1 turn of this same conversation, and Phase 1 notes (including which ground-truth items the v1 docs mention) were in my context. I did not code to them, and no element name from the CSV is in the code, but I cannot prove I was unaffected. Treat the result as "built blind to the file", not "never seen".

## Run
| | |
|---|---|
| Command | `truthlayer run --auto-approve-high` on the real `docs/v1` against v1 (STU3) and v2 (R4) |
| Wall-clock time | **0.34 s** for the pipeline (0.47 s including Python start-up) |
| AI used | **No. MOCK mode** (no `ANTHROPIC_API_KEY` in this environment) |
| AI cost | **$0.00** (0 tokens). Live cost not measured. |
| Scanned | 401 booklet pieces, 82 element mentions, 80 v1-vs-v2 differences |

## Findings by label
| Label | Count |
|---|---|
| WRONG | 8 |
| GHOST | 1 |
| EXAMPLE | 5 |
| MISSING | 51 |
| **Total** | **65** (20 HIGH confidence, 45 LOW / "ask a human") |

Also: 25 fix proposals (7 HIGH-confidence ones auto-approved with approver `auto`, 18 left PENDING), 24 pages published, 23 style findings.

## Score against the 35 CMS-listed changes
"Caught" = at least one finding names that element (match is by resource + element name, a loose test; see caveats).

| Result | Count |
|---|---|
| Caught by a finding | **21 / 35** |
| In the v1/v2 difference list but no finding was raised | 2 (`Eob.hospitalization`, `Patient.animal`: removed, never mentioned in the booklet, so nothing to correct) |
| Missed completely | 12 |
| **Recall (caught by a finding)** | **60%** (21/35) |
| Recall counting the 2 above as "seen" | 66% (23/35) |

Caught rows by label (a row can have several): MISSING 15, WRONG 5, EXAMPLE 5, GHOST 0.
**Only 9 of the 21 catches point at actual booklet text** (WRONG or EXAMPLE). The other 12 were caught only as MISSING ("v2 has/changes this; the booklet is silent"). That is real, but it is a weaker kind of catch.

### Which of the 35 were missed, and why
| CMS change | Why the tool missed it |
|---|---|
| `Patient.active`, `Patient.gender`, `Patient.generalPractitioner`, `Patient.identifier.type` value-set/default changes (CHG-017 to 020) | The tool compares type and cardinality only. It does not compare value-set bindings or defaults. |
| `Patient.identifier` slicing and hashed-vs-unhashed MBI/HICN (CHG-021, 022) | Slicing and identifier policy are profile rules, not in the base definitions. |
| `IncludeIdentifiers` header (CHG-023) | HTTP headers are in no machine-readable file we have. |
| `Eob.referral` optional → mandatory (CHG-009) | Cardinality did not change in the base definitions; only the allowed target type did, and the tool ignores targets. |
| `Coverage.class.name`, `.type`, `.value`, `costToBeneficiary.type` (CHG-031, 033, 034, 035) | `Coverage.class` is new in v2, so the tool reports only the top element and folds its children into it ("collapsed descendants"). Their parents were caught. |

## Precision and false alarms
- **Strict precision: 43%** (28 of 65 findings match a CMS-listed change).
- The other 37 findings are not on CMS's list. I checked each one:
  - **33 are real v1→v2 differences CMS did not list.** They come straight from the official R3 and R4 definitions: about 20 new v2 elements, several elements that became required (`ExplanationOfBenefit.created`, `.status`, `.insurer`, `.insurance`), the type change on `.form`, the new v2 search parameters, the `ReferralRequest` resource that no longer exists, and 4 plausible renames (`informationLinkId`→`informationSequence`, `procedureLinkId`→`procedureSequence`, `sequenceLinkId`→`itemSequence`, `totalCost`→`total`). CMS's own page says "approximately 35" EOB elements were added and names only a few.
  - **4 are true false alarms:** three bad rename guesses (`category`→`factor` twice, `totalBenefit`→`benefitPeriod`; all marked LOW / ask a human) and one wrong match (`ExplanationOfBenefit.insurance.coverage` flagged because the booklet's prose at `blue-button-v1-stu3-docs.md:214` talks about the Coverage endpoint, not that element).
- So: **about 94% of findings (61 of 65) are real drift**, but only 43% are on CMS's list. The "real" call is my reading of the FHIR R3/R4 definitions, not CMS's word.
- **Volume problem:** 51 of 65 findings are MISSING, mostly optional additions. They are true but low-value. They drown the 14 findings that point at booklet text.

## Five example findings in plain English
1. **Renamed field (WRONG, LOW, ask a human)** `explanation-of-benefits-fhir.md:108`. The old booklet lists `careTeamLinkId` as a field of an EOB item. In v2 the same slot is `careTeamSequence` (same type, same 0..* count). CMS lists this rename. The tool can only guess it from the similar names.
2. **Resource that no longer exists (GHOST, HIGH)** `explanation-of-benefits-fhir.md:25` and `blue-button-v1-stu3-docs.md:421`. The booklet says an EOB entry can contain a `ReferralRequest`. FHIR R4 has no such resource type. CMS did not list this.
3. **Old sample (EXAMPLE, HIGH)** `data/v1/sample-coverage-entry.json:75`. The sample shows a `grouping` block with `subGroup` and `subPlan`. v2 has no `grouping`; its place is taken by `class`. CMS lists this.
4. **Now required (WRONG, HIGH)** `explanation-of-benefits-fhir.md:87-89`. The booklet lists `status`, `type` and `patient` as fields with no hint they always appear. In v2 all three are required (0..1 became 1..1). CMS lists `patient` only.
5. **A false alarm (WRONG, HIGH, wrong)** `blue-button-v1-stu3-docs.md:214`. The booklet says to get data from the "Patient endpoint" and the "Coverage" resource. The tool matched the word Coverage to `ExplanationOfBenefit.insurance.coverage` and said that field's count changed. The count did change, but the booklet is not talking about that field. A word-in-context mistake.

## What this does not show
- This is one real booklet (2 pages, 1 JSON sample set) against one CMS list written from CMS statements, so the numbers are small-sample.
- Fixes ran in MOCK mode. Nothing here measures how good the AI fixer is.
- "Caught" uses a loose resource+name match, so it can credit a finding that says something different about the same element (for example `Eob.use`, caught only through an unrelated added-element finding).

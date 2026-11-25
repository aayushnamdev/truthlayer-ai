# TruthLayer AI results, third score

`results.md` (first score) and `results-v2.md` (second score) are unchanged. Detection (recall) did not change in this round; what changed is what the findings are called.

## How fair is this score?
- Scores two and three are **not blind**: I had already seen CMS's list. The NEEDS_NOTE change was prompted by what the AI run showed (most "WRONG" passages were bare field names with nothing false in them), not by the CMS list.
- NEEDS_NOTE is decided by a plain word check on the passage (`truthlayer/claims.py`), not by AI. It looks for words about the rule that changed (for example "optional" or "required" for a cardinality change, "value set" for a binding change). If none appear, the passage only names the field.

## First vs second vs third
| Measure | First (blind) | Second | Third |
|---|---|---|---|
| CMS changes caught by a finding | 21 of 35 (60%) | 32 of 35 (91%) | 32 of 35 (91%) |
| Missed | 12 | 1 | 1 (`IncludeIdentifiers` header) |
| Findings in total | 65 | 155 | 155 |
| WRONG (text states something now false) | 8 | 20 | **3** |
| NEEDS_NOTE (text only names a changed field) | n/a | n/a | **17** |
| GHOST | 1 | 1 | 1 |
| EXAMPLE | 5 | 12 | 12 |
| MISSING | 51 | 112 | 112 |
| UNVERIFIABLE | n/a | 10 | 10 |
| Severity (critical / high / medium / low) | n/a | 9 / 22 / 39 / 85 | **4 / 11 / 45 / 95** |
| Catches pointing at a false statement (WRONG, GHOST or EXAMPLE) | 9 of 21 | 17 of 32 (WRONG or EXAMPLE) | 14 of 32, plus 3 NEEDS_NOTE |
| Precision of CRITICAL + HIGH findings | n/a | 13 of 31 (42%) | **10 of 15 (67%)** |
| Strict precision, all findings | 43% (28 of 65) | 28% (43 of 155) | 28% (43 of 155) |
| Run time | 0.34 s | 0.63 s | about 0.6 s |
| Real AI cost | $0 (MOCK) | $0.04 (25 calls) | $0.06 total at assumed prices (32 calls) |

Reading it: the same 32 CMS changes are caught, but the "Fix these first" list is now much shorter and truer. The 15 CRITICAL and HIGH findings are now mostly renamed names (3), ghost resources (1) and wrong samples (11); fields that only have a changed rule moved to NEEDS_NOTE.

## What changed since the second score
1. New label **NEEDS_NOTE** (severity MEDIUM for now-required, cardinality, value-set, type or target changes, LOW for minor ones). It is not sent to the AI fixer and is not in "Fix these first".
2. **WRONG** now means the passage states something false. Renamed names always count. For other rule changes the passage must say something about that rule (word check).
3. Fixer: new `truthlayer fix --live --retry-unparseable` (extra caps: 7 calls, $0.10).
4. Dashboard has a NEEDS_NOTE filter; `truthlayer app --host 0.0.0.0` for other devices.

## Retry of the 7 unreadable AI replies (shorter-reason prompt)
- 7 calls, 3,359 input and 2,477 output tokens: about **$0.016** at assumed prices ($0.031 as charged to the budget, which doubles prices). Allowed was 7 calls and $0.10 more, so well inside both. Model: claude-haiku-5-5 only.
- Results: **1 fixed** (a sample key `service` became `productOrService`), **1 correctly left unchanged** (the model said the passage shows only the reference, so the cardinality change makes no word wrong), **5 still unreadable**.
- Why the 5 still fail: all five are JSON sample passages. The model rewrites the whole passage with escaped quotes and runs into the 400-token output cap before it finishes the JSON. A shorter reason does not help there. A real fix is to ask for a small edit (old text, new text) instead of the whole passage. I did not do that because the extra calls are used up.
- Total real AI use across the project: 32 calls, 12,286 input and 9,502 output tokens, about $0.06 at assumed prices. The $1.00 limit was never near.

## Fix these first (real run)
CRITICAL: `item.careTeamLinkId` to `careTeamSequence`; `item.diagnosisLinkId` to `diagnosisSequence`; `item.service` to `productOrService`; the `ReferralRequest` resource no longer exists.
HIGH, all wrong samples: `addItem.service`, `Coverage.grouping`, `Coverage.beneficiary`, `Coverage.status`, `Coverage.type`, `ExplanationOfBenefit.created`, `item.adjudication.category`, `item.adjudication.reason`, `Patient.address`, `Patient.gender`, `Patient.identifier`.

## Still true
- 1 CMS change is missed (the `IncludeIdentifiers` header: the booklet never mentions it).
- The two removed-and-never-mentioned items (`Eob.hospitalization`, `Patient.animal`) have no finding because there is no text to fix.
- Strict precision stays low because many real differences are not on CMS's list.

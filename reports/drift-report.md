# Drift report

## In plain English

We compared the old v1 booklet with the v1 and v2 API definitions. We found **65 places where the booklet may be out of date** (8 wrong, 1 describing things that no longer exist, 5 in examples only, 51 things v2 has that the booklet never mentions). 20 are high confidence; 45 are marked "ask a human".

- **WRONG**: the text names something that still exists in v2 but changed (or was probably renamed).
- **GHOST**: the text describes something that is gone in v2.
- **EXAMPLE**: only a sample/code block shows the old name; the prose does not.
- **MISSING**: v2 adds or changes it and the booklet is silent.

Scanned 401 pieces of the booklet, found 82 element mentions, and compared 80 differences between the v1 and v2 definitions.
Style check: 23 findings (see JSON).

## WRONG (8)

| ID | Confidence | Element (v1 → v2) | Where | What |
|---|---|---|---|---|
| F-004 | LOW (ask a human) | `ExplanationOfBenefit.item.diagnosisLinkId` → `ExplanationOfBenefit.item.diagnosisSequence` | docs/v1/explanation-of-benefits-fhir.md:109 | diagnosisLinkId may have become diagnosisSequence (similarity 0.725) |
| F-007 | LOW (ask a human) | `ExplanationOfBenefit.item.service` → `ExplanationOfBenefit.item.productOrService` | docs/v1/blue-button-v1-stu3-docs.md:850 | service may have become productOrService (similarity 0.709) |
| F-011 | LOW (ask a human) | `ExplanationOfBenefit.item.careTeamLinkId` → `ExplanationOfBenefit.item.careTeamSequence` | docs/v1/explanation-of-benefits-fhir.md:108 | careTeamLinkId may have become careTeamSequence (similarity 0.7) |
| F-052 | HIGH | `ExplanationOfBenefit.insurance` → `ExplanationOfBenefit.insurance` | docs/v1/blue-button-v1-stu3-docs.md:214 | cardinality 0..1 -> 1..* |
| F-053 | HIGH | `ExplanationOfBenefit.insurance.coverage` → `ExplanationOfBenefit.insurance.coverage` | docs/v1/blue-button-v1-stu3-docs.md:214 | cardinality 0..1 -> 1..1 |
| F-056 | HIGH | `ExplanationOfBenefit.patient` → `ExplanationOfBenefit.patient` | docs/v1/blue-button-v1-stu3-docs.md:591 | cardinality 0..1 -> 1..1 |
| F-059 | HIGH | `ExplanationOfBenefit.status` → `ExplanationOfBenefit.status` | docs/v1/explanation-of-benefits-fhir.md:87 | cardinality 0..1 -> 1..1 |
| F-061 | HIGH | `ExplanationOfBenefit.type` → `ExplanationOfBenefit.type` | docs/v1/explanation-of-benefits-fhir.md:88 | cardinality 0..1 -> 1..1 |

## GHOST (1)

| ID | Confidence | Element (v1 → v2) | Where | What |
|---|---|---|---|---|
| F-065 | HIGH | `ReferralRequest` → `-` | docs/v1/blue-button-v1-stu3-docs.md:421 | resource type does not exist in the v2 release |

## EXAMPLE (5)

| ID | Confidence | Element (v1 → v2) | Where | What |
|---|---|---|---|---|
| F-001 | LOW (ask a human) | `ExplanationOfBenefit.addItem.service` → `ExplanationOfBenefit.addItem.serviced[x]` | docs/v1/blue-button-v1-stu3-docs.md:850 | service may have become serviced[x] (similarity 0.933) |
| F-016 | HIGH | `Coverage.grouping` → `-` | data/v1/sample-coverage-entry.json:75 | not in v2 |
| F-047 | HIGH | `Coverage.beneficiary` → `Coverage.beneficiary` | data/v1/sample-coverage-entry.json:72 | cardinality 0..1 -> 1..1 |
| F-049 | HIGH | `Coverage.status` → `Coverage.status` | data/v1/sample-coverage-entry.json:63 | cardinality 0..1 -> 1..1 |
| F-050 | HIGH | `ExplanationOfBenefit.created` → `ExplanationOfBenefit.created` | docs/v1/blue-button-v1-stu3-docs.md:590 | cardinality 0..1 -> 1..1 |

## MISSING (51)

| ID | Confidence | Element (v1 → v2) | Where | What |
|---|---|---|---|---|
| F-002 | LOW (ask a human) | `ExplanationOfBenefit.item.informationLinkId` → `ExplanationOfBenefit.item.informationSequence` | - | informationLinkId may have become informationSequence (similarity 0.767) |
| F-003 | LOW (ask a human) | `ExplanationOfBenefit.item.procedureLinkId` → `ExplanationOfBenefit.item.procedureSequence` | - | procedureLinkId may have become procedureSequence (similarity 0.725) |
| F-005 | LOW (ask a human) | `ExplanationOfBenefit.addItem.sequenceLinkId` → `ExplanationOfBenefit.addItem.itemSequence` | - | sequenceLinkId may have become itemSequence (similarity 0.715) |
| F-006 | LOW (ask a human) | `ExplanationOfBenefit.totalCost` → `ExplanationOfBenefit.total` | - | totalCost may have become total (similarity 0.714) |
| F-008 | LOW (ask a human) | `ExplanationOfBenefit.item.detail.subDetail.service` → `ExplanationOfBenefit.item.detail.subDetail.productOrService` | - | service may have become productOrService (similarity 0.709) |
| F-009 | LOW (ask a human) | `ExplanationOfBenefit.item.detail.service` → `ExplanationOfBenefit.item.detail.productOrService` | - | service may have become productOrService (similarity 0.709) |
| F-010 | LOW (ask a human) | `ExplanationOfBenefit.addItem.detail.service` → `ExplanationOfBenefit.addItem.detail.productOrService` | - | service may have become productOrService (similarity 0.709) |
| F-012 | LOW (ask a human) | `ExplanationOfBenefit.organization` → `ExplanationOfBenefit.adjudication` | - | organization may have become adjudication (similarity 0.583) |
| F-013 | LOW (ask a human) | `ExplanationOfBenefit.addItem.detail.category` → `ExplanationOfBenefit.addItem.detail.factor` | - | category may have become factor (similarity 0.571) |
| F-014 | LOW (ask a human) | `ExplanationOfBenefit.addItem.category` → `ExplanationOfBenefit.addItem.factor` | - | category may have become factor (similarity 0.571) |
| F-015 | LOW (ask a human) | `ExplanationOfBenefit.totalBenefit` → `ExplanationOfBenefit.benefitPeriod` | - | totalBenefit may have become benefitPeriod (similarity 0.56) |
| F-017 | LOW (ask a human) | `-` → `Coverage.class` | - | new in v2 |
| F-018 | LOW (ask a human) | `-` → `Coverage.costToBeneficiary` | - | new in v2 |
| F-019 | LOW (ask a human) | `-` → `Coverage.subrogation` | - | new in v2 |
| F-020 | LOW (ask a human) | `-` → `ExplanationOfBenefit.addItem.bodySite` | - | new in v2 |
| F-021 | LOW (ask a human) | `-` → `ExplanationOfBenefit.addItem.detail.net` | - | new in v2 |
| F-022 | LOW (ask a human) | `-` → `ExplanationOfBenefit.addItem.detail.quantity` | - | new in v2 |
| F-023 | LOW (ask a human) | `-` → `ExplanationOfBenefit.addItem.detail.subDetail` | - | new in v2 |
| F-024 | LOW (ask a human) | `-` → `ExplanationOfBenefit.addItem.detail.unitPrice` | - | new in v2 |
| F-025 | LOW (ask a human) | `-` → `ExplanationOfBenefit.addItem.detailSequence` | - | new in v2 |
| F-026 | LOW (ask a human) | `-` → `ExplanationOfBenefit.addItem.location[x]` | - | new in v2 |
| F-027 | LOW (ask a human) | `-` → `ExplanationOfBenefit.addItem.net` | - | new in v2 |
| F-028 | HIGH | `-` → `ExplanationOfBenefit.addItem.productOrService` | - | new in v2 |
| F-029 | LOW (ask a human) | `-` → `ExplanationOfBenefit.addItem.programCode` | - | new in v2 |
| F-030 | LOW (ask a human) | `-` → `ExplanationOfBenefit.addItem.provider` | - | new in v2 |
| F-031 | LOW (ask a human) | `-` → `ExplanationOfBenefit.addItem.quantity` | - | new in v2 |
| F-032 | LOW (ask a human) | `-` → `ExplanationOfBenefit.addItem.subDetailSequence` | - | new in v2 |
| F-033 | LOW (ask a human) | `-` → `ExplanationOfBenefit.addItem.subSite` | - | new in v2 |
| F-034 | LOW (ask a human) | `-` → `ExplanationOfBenefit.addItem.unitPrice` | - | new in v2 |
| F-035 | LOW (ask a human) | `-` → `ExplanationOfBenefit.diagnosis.onAdmission` | - | new in v2 |
| F-036 | LOW (ask a human) | `-` → `ExplanationOfBenefit.formCode` | - | new in v2 |
| F-037 | LOW (ask a human) | `-` → `ExplanationOfBenefit.fundsReserve` | - | new in v2 |
| F-038 | LOW (ask a human) | `-` → `ExplanationOfBenefit.fundsReserveRequested` | - | new in v2 |
| F-039 | HIGH | `-` → `ExplanationOfBenefit.insurance.focal` | - | new in v2 |
| F-040 | LOW (ask a human) | `-` → `ExplanationOfBenefit.preAuthRef` | - | new in v2 |
| F-041 | LOW (ask a human) | `-` → `ExplanationOfBenefit.preAuthRefPeriod` | - | new in v2 |
| F-042 | LOW (ask a human) | `-` → `ExplanationOfBenefit.priority` | - | new in v2 |
| F-043 | LOW (ask a human) | `-` → `ExplanationOfBenefit.procedure.type` | - | new in v2 |
| F-044 | LOW (ask a human) | `-` → `ExplanationOfBenefit.procedure.udi` | - | new in v2 |
| F-045 | LOW (ask a human) | `-` → `ExplanationOfBenefit.supportingInfo` | - | new in v2 |

_11 more in drift-report.json._


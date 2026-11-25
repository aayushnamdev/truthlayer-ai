# Drift report

## In plain English

We compared the old v1 booklet with the v1 and v2 API definitions. We found **155 places where the booklet may be out of date or unprovable**: 4 critical, 11 high, 45 medium, 95 low. 59 are high confidence; 96 are marked "ask a human".

By label: 3 wrong, 1 ghost, 12 example, 17 needs-note, 112 missing, 10 unverifiable.

- **WRONG**: the text states something that is now false (a renamed name, or a claim about a rule that changed).
- **NEEDS_NOTE**: the text only names a field whose rules changed and says nothing false; a writer should add the rule.
- **GHOST**: the text describes something that is gone in v2.
- **EXAMPLE**: only a sample/code block shows the old name.
- **MISSING**: v2 adds or changes it and the booklet is silent.
- **UNVERIFIABLE**: a header or policy statement no specification can prove.

Scanned 401 pieces of the booklet, found 77 element mentions, and compared 160 differences between the v1 and v2 definitions. Style check: 23 findings (see JSON).

## Fix these first (15 of 15 critical/high)

1. **CRITICAL** · WRONG · HIGH · `ExplanationOfBenefit.item.careTeamLinkId` · docs/v1/explanation-of-benefits-fhir.md:108  
   The old booklet talks about `ExplanationOfBenefit.item.careTeamLinkId` (docs/v1/explanation-of-benefits-fhir.md:108). In v2 it is now `ExplanationOfBenefit.item.careTeamSequence` (confirmed by HL7's official map).
1. **CRITICAL** · WRONG · HIGH · `ExplanationOfBenefit.item.diagnosisLinkId` · docs/v1/explanation-of-benefits-fhir.md:109  
   The old booklet talks about `ExplanationOfBenefit.item.diagnosisLinkId` (docs/v1/explanation-of-benefits-fhir.md:109). In v2 it is now `ExplanationOfBenefit.item.diagnosisSequence` (confirmed by HL7's official map).
1. **CRITICAL** · GHOST · HIGH · `ReferralRequest` · docs/v1/blue-button-v1-stu3-docs.md:421  
   The old booklet describes `ReferralRequest` (docs/v1/blue-button-v1-stu3-docs.md:421), which does not exist in v2 (resource type does not exist in the v2 release).
1. **CRITICAL** · WRONG · LOW (ask a human) · `ExplanationOfBenefit.item.service` · docs/v1/blue-button-v1-stu3-docs.md:850  
   The old booklet talks about `ExplanationOfBenefit.item.service` (docs/v1/blue-button-v1-stu3-docs.md:850). In v2 it is now `ExplanationOfBenefit.item.productOrService` (confirmed by HL7's official map).
1. **HIGH** · EXAMPLE · HIGH · `Coverage.grouping` · data/v1/sample-coverage-entry.json:75  
   A sample in the old booklet (data/v1/sample-coverage-entry.json:75) shows `Coverage.grouping`, which v2 changed or removed (not in v2).
1. **HIGH** · EXAMPLE · HIGH · `Coverage.beneficiary` · data/v1/sample-coverage-entry.json:72  
   A sample in the old booklet (data/v1/sample-coverage-entry.json:72) shows `Coverage.beneficiary`, which v2 changed or removed (cardinality 0..1 -> 1..1; profile: must-support False -> True).
1. **HIGH** · EXAMPLE · HIGH · `Coverage.status` · data/v1/sample-coverage-entry.json:63  
   A sample in the old booklet (data/v1/sample-coverage-entry.json:63) shows `Coverage.status`, which v2 changed or removed (cardinality 0..1 -> 1..1; value set version http://hl7.org/fhir/ValueSet/fm-status -> http://hl7.org/fhir/ValueSet/fm-status|4.0.1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-fm-status -> http://hl7.org/fhir/ValueSet/fm-status|4.0.1; profile: must-support False -> True).
1. **HIGH** · EXAMPLE · HIGH · `Coverage.type` · data/v1/sample-coverage-entry.json:64  
   A sample in the old booklet (data/v1/sample-coverage-entry.json:64) shows `Coverage.type`, which v2 changed or removed (profile: cardinality 1..1 -> 0..1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-coverage-type -> http://hl7.org/fhir/ValueSet/coverage-type).
1. **HIGH** · EXAMPLE · HIGH · `ExplanationOfBenefit.item.adjudication.category` · docs/v1/explanation-of-benefits-fhir.md:159  
   A sample in the old booklet (docs/v1/explanation-of-benefits-fhir.md:159) shows `ExplanationOfBenefit.item.adjudication.category`, which v2 changed or removed (profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-adjudication -> http://hl7.org/fhir/us/carin-bb/ValueSet/C4BBAdjudicationCategoryDiscriminator; profile: binding strength example -> required).
1. **HIGH** · EXAMPLE · HIGH · `ExplanationOfBenefit.item.adjudication.reason` · docs/v1/explanation-of-benefits-fhir.md:168  
   A sample in the old booklet (docs/v1/explanation-of-benefits-fhir.md:168) shows `ExplanationOfBenefit.item.adjudication.reason`, which v2 changed or removed (profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-adjudication-reason -> http://hl7.org/fhir/ValueSet/adjudication-reason).
1. **HIGH** · EXAMPLE · HIGH · `Patient.address` · docs/v1/blue-button-v1-stu3-docs.md:491  
   A sample in the old booklet (docs/v1/blue-button-v1-stu3-docs.md:491) shows `Patient.address`, which v2 changed or removed (profile: cardinality 1..* -> 0..*).
1. **HIGH** · EXAMPLE · HIGH · `Patient.gender` · docs/v1/blue-button-v1-stu3-docs.md:489  
   A sample in the old booklet (docs/v1/blue-button-v1-stu3-docs.md:489) shows `Patient.gender`, which v2 changed or removed (value set version http://hl7.org/fhir/ValueSet/administrative-gender -> http://hl7.org/fhir/ValueSet/administrative-gender|4.0.1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-gndr-cd -> http://hl7.org/fhir/ValueSet/administrative-gender).
1. **HIGH** · EXAMPLE · HIGH · `Patient.identifier` · docs/v1/blue-button-v1-stu3-docs.md:469  
   A sample in the old booklet (docs/v1/blue-button-v1-stu3-docs.md:469) shows `Patient.identifier`, which v2 changed or removed (profile: slicing 'none' -> 'sliced by pattern:type; required slices: memberid').
1. **HIGH** · EXAMPLE · LOW (ask a human) · `ExplanationOfBenefit.addItem.service` · docs/v1/blue-button-v1-stu3-docs.md:850  
   A sample in the old booklet (docs/v1/blue-button-v1-stu3-docs.md:850) shows `ExplanationOfBenefit.addItem.service`, which v2 changed or removed (service may have become serviced[x] (similarity 0.933)).
1. **HIGH** · EXAMPLE · LOW (ask a human) · `ExplanationOfBenefit.created` · docs/v1/blue-button-v1-stu3-docs.md:590  
   A sample in the old booklet (docs/v1/blue-button-v1-stu3-docs.md:590) shows `ExplanationOfBenefit.created`, which v2 changed or removed (cardinality 0..1 -> 1..1; profile: must-support False -> True).

## WRONG (3)

| ID | Severity | Confidence | Element (v1 → v2) | Where | What |
|---|---|---|---|---|---|
| F-002 | CRITICAL | HIGH | `ExplanationOfBenefit.item.careTeamLinkId` → `ExplanationOfBenefit.item.careTeamSequence` | docs/v1/explanation-of-benefits-fhir.md:108 | careTeamLinkId was renamed careTeamSequence (HL7 R3-R4 map) |
| F-003 | CRITICAL | HIGH | `ExplanationOfBenefit.item.diagnosisLinkId` → `ExplanationOfBenefit.item.diagnosisSequence` | docs/v1/explanation-of-benefits-fhir.md:109 | diagnosisLinkId was renamed diagnosisSequence (HL7 R3-R4 map) |
| F-006 | CRITICAL | LOW (ask a human) | `ExplanationOfBenefit.item.service` → `ExplanationOfBenefit.item.productOrService` | docs/v1/blue-button-v1-stu3-docs.md:850 | service was renamed productOrService (HL7 R3-R4 map) |

## GHOST (1)

| ID | Severity | Confidence | Element (v1 → v2) | Where | What |
|---|---|---|---|---|---|
| F-145 | CRITICAL | HIGH | `ReferralRequest` → `-` | docs/v1/blue-button-v1-stu3-docs.md:421 | resource type does not exist in the v2 release |

## EXAMPLE (12)

| ID | Severity | Confidence | Element (v1 → v2) | Where | What |
|---|---|---|---|---|---|
| F-008 | HIGH | LOW (ask a human) | `ExplanationOfBenefit.addItem.service` → `ExplanationOfBenefit.addItem.serviced[x]` | docs/v1/blue-button-v1-stu3-docs.md:850 | service may have become serviced[x] (similarity 0.933) |
| F-016 | HIGH | HIGH | `Coverage.grouping` → `-` | data/v1/sample-coverage-entry.json:75 | not in v2 |
| F-047 | HIGH | HIGH | `Coverage.beneficiary` → `Coverage.beneficiary` | data/v1/sample-coverage-entry.json:72 | cardinality 0..1 -> 1..1; profile: must-support False -> True |
| F-052 | HIGH | HIGH | `Coverage.status` → `Coverage.status` | data/v1/sample-coverage-entry.json:63 | cardinality 0..1 -> 1..1; value set version http://hl7.org/fhir/ValueSet/fm-status -> http://hl7.org/fhir/ValueSet/fm-status|4.0.1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-fm-status -> http://hl7.org/fhir/ValueSet/fm-status|4.0.1; profile: must-support False -> True |
| F-054 | HIGH | HIGH | `Coverage.type` → `Coverage.type` | data/v1/sample-coverage-entry.json:64 | profile: cardinality 1..1 -> 0..1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-coverage-type -> http://hl7.org/fhir/ValueSet/coverage-type |
| F-070 | HIGH | LOW (ask a human) | `ExplanationOfBenefit.created` → `ExplanationOfBenefit.created` | docs/v1/blue-button-v1-stu3-docs.md:590 | cardinality 0..1 -> 1..1; profile: must-support False -> True |
| F-084 | HIGH | HIGH | `ExplanationOfBenefit.item.adjudication.category` → `ExplanationOfBenefit.item.adjudication.category` | docs/v1/explanation-of-benefits-fhir.md:159 | profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-adjudication -> http://hl7.org/fhir/us/carin-bb/ValueSet/C4BBAdjudicationCategoryDiscriminator; profile: binding strength example -> required |
| F-085 | HIGH | HIGH | `ExplanationOfBenefit.item.adjudication.reason` → `ExplanationOfBenefit.item.adjudication.reason` | docs/v1/explanation-of-benefits-fhir.md:168 | profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-adjudication-reason -> http://hl7.org/fhir/ValueSet/adjudication-reason |
| F-130 | HIGH | HIGH | `Patient.address` → `Patient.address` | docs/v1/blue-button-v1-stu3-docs.md:491 | profile: cardinality 1..* -> 0..* |
| F-136 | HIGH | HIGH | `Patient.gender` → `Patient.gender` | docs/v1/blue-button-v1-stu3-docs.md:489 | value set version http://hl7.org/fhir/ValueSet/administrative-gender -> http://hl7.org/fhir/ValueSet/administrative-gender|4.0.1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-gndr-cd -> http://hl7.org/fhir/ValueSet/administrative-gender |
| F-138 | HIGH | HIGH | `Patient.identifier` → `Patient.identifier` | docs/v1/blue-button-v1-stu3-docs.md:469 | profile: slicing 'none' -> 'sliced by pattern:type; required slices: memberid' |
| F-131 | MEDIUM | HIGH | `Patient.birthDate` → `Patient.birthDate` | docs/v1/blue-button-v1-stu3-docs.md:490 | profile: must-support False -> True |

## NEEDS_NOTE (17)

| ID | Severity | Confidence | Element (v1 → v2) | Where | What |
|---|---|---|---|---|---|
| F-071 | MEDIUM | HIGH | `ExplanationOfBenefit.diagnosis` → `ExplanationOfBenefit.diagnosis` | docs/v1/explanation-of-benefits-fhir.md:94 | profile: cardinality 0..* -> 1..*; profile: must-support False -> True |
| F-078 | MEDIUM | HIGH | `ExplanationOfBenefit.insurance` → `ExplanationOfBenefit.insurance` | docs/v1/explanation-of-benefits-fhir.md:95 | cardinality 0..1 -> 1..* |
| F-087 | MEDIUM | HIGH | `ExplanationOfBenefit.item.category` → `ExplanationOfBenefit.item.category` | docs/v1/explanation-of-benefits-fhir.md:110 | value set http://hl7.org/fhir/ValueSet/benefit-subcategory -> http://hl7.org/fhir/ValueSet/ex-benefitcategory |
| F-107 | MEDIUM | HIGH | `ExplanationOfBenefit.patient` → `ExplanationOfBenefit.patient` | docs/v1/blue-button-v1-stu3-docs.md:591 | cardinality 0..1 -> 1..1 |
| F-122 | MEDIUM | HIGH | `ExplanationOfBenefit.referral` → `ExplanationOfBenefit.referral` | docs/v1/explanation-of-benefits-fhir.md:91 | reference targets ReferralRequest -> ServiceRequest |
| F-126 | MEDIUM | HIGH | `ExplanationOfBenefit.status` → `ExplanationOfBenefit.status` | docs/v1/explanation-of-benefits-fhir.md:87 | cardinality 0..1 -> 1..1; value set version http://hl7.org/fhir/ValueSet/explanationofbenefit-status -> http://hl7.org/fhir/ValueSet/explanationofbenefit-status|4.0.1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-explanationofbenefit-status -> http://hl7.org/fhir/ValueSet/explanationofbenefit-status|4.0.1 |
| F-128 | MEDIUM | HIGH | `ExplanationOfBenefit.type` → `ExplanationOfBenefit.type` | docs/v1/explanation-of-benefits-fhir.md:88 | cardinality 0..1 -> 1..1; binding strength required -> extensible; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-claim-type -> http://hl7.org/fhir/ValueSet/claim-type; profile: fixed/default value (none) -> patternCodeableConcept={"coding": [{"code": "institutional", "system": "http://terminology.hl7.org/CodeSystem/claim-type"}]} |
| F-064 | LOW | HIGH | `ExplanationOfBenefit.billablePeriod` → `ExplanationOfBenefit.billablePeriod` | docs/v1/explanation-of-benefits-fhir.md:90 | profile: must-support False -> True |
| F-065 | LOW | HIGH | `ExplanationOfBenefit.careTeam` → `ExplanationOfBenefit.careTeam` | docs/v1/explanation-of-benefits-fhir.md:93 | profile: cardinality 1..* -> 0..* |
| F-075 | LOW | HIGH | `ExplanationOfBenefit.disposition` → `ExplanationOfBenefit.disposition` | docs/v1/explanation-of-benefits-fhir.md:92 | profile: cardinality 1..1 -> 0..1; profile: must-support True -> False |
| F-081 | LOW | LOW (ask a human) | `ExplanationOfBenefit.item` → `ExplanationOfBenefit.item` | docs/v1/blue-button-v1-stu3-docs.md:850 | profile: cardinality 1..* -> 0..* |
| F-082 | LOW | HIGH | `ExplanationOfBenefit.item.adjudication` → `ExplanationOfBenefit.item.adjudication` | docs/v1/explanation-of-benefits-fhir.md:116 | profile: cardinality 1..* -> 2..*; profile: slicing 'none' -> 'sliced by pattern:category; required slices: adjudicationamounttype, inoutnetwork' |
| F-098 | LOW | HIGH | `ExplanationOfBenefit.item.location[x]` → `ExplanationOfBenefit.item.location[x]` | docs/v1/explanation-of-benefits-fhir.md:114 | profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-service-place -> http://hl7.org/fhir/ValueSet/service-place; profile: slicing 'sliced by ?' -> 'none' |
| F-099 | LOW | HIGH | `ExplanationOfBenefit.item.modifier` → `ExplanationOfBenefit.item.modifier` | docs/v1/explanation-of-benefits-fhir.md:112 | profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-claim-modifiers -> http://hl7.org/fhir/us/carin-bb/ValueSet/AMACPTCMSHCPCSModifiers; profile: binding strength example -> required; profile: must-support False -> True |
| F-102 | LOW | HIGH | `ExplanationOfBenefit.item.quantity` → `ExplanationOfBenefit.item.quantity` | docs/v1/explanation-of-benefits-fhir.md:115 | profile: cardinality 1..1 -> 0..1 |
| F-104 | LOW | HIGH | `ExplanationOfBenefit.item.serviced[x]` → `ExplanationOfBenefit.item.serviced[x]` | docs/v1/explanation-of-benefits-fhir.md:113 | profile: cardinality 1..1 -> 0..1; profile: slicing 'sliced by ?' -> 'sliced by type:$this' |
| F-111 | LOW | HIGH | `ExplanationOfBenefit.payment` → `ExplanationOfBenefit.payment` | docs/v1/explanation-of-benefits-fhir.md:97 | profile: cardinality 1..1 -> 0..1; profile: must-support False -> True |

## MISSING, medium (36)

- F-001 `ExplanationOfBenefit.supportingInfo`: information was renamed supportingInfo (HL7 R3-R4 map) (+6 child elements: category, code, reason, sequence, timing[x], value[x])
- F-007 `ExplanationOfBenefit.total`: totalBenefit was renamed total (HL7 R3-R4 map)
- F-010 `ExplanationOfBenefit.item.detail.subDetail.productOrService`: service may have become productOrService (similarity 0.709)
- F-011 `ExplanationOfBenefit.item.detail.productOrService`: service may have become productOrService (similarity 0.709)
- F-012 `ExplanationOfBenefit.addItem.detail.productOrService`: service may have become productOrService (similarity 0.709)
- F-017 `Coverage.class`: new in v2 (+3 child elements: name, type, value)
- F-018 `Coverage.costToBeneficiary`: new in v2 (+5 child elements: exception, period, type, type, value[x])
- F-023 `ExplanationOfBenefit.addItem.detail.subDetail`: new in v2 (+8 child elements: adjudication, factor, modifier, net, noteNumber, productOrService, quantity, unitPrice)
- F-028 `ExplanationOfBenefit.addItem.productOrService`: new in v2
- F-040 `ExplanationOfBenefit.insurance.focal`: new in v2
- F-044 `ExplanationOfBenefit.procedure.type`: new in v2
- F-046 `ExplanationOfBenefit.use`: new in v2
- F-049 `Coverage.payor`: cardinality 0..* -> 1..*; profile: must-support False -> True
- F-051 `Coverage.relationship`: value set http://hl7.org/fhir/ValueSet/policyholder-relationship -> http://hl7.org/fhir/ValueSet/subscriber-relationship; binding strength example -> extensible; profile: cardinality 0..1 -> 1..1; profile: must-support False -> True
- F-053 `Coverage.subscriberId`: profile: cardinality 0..1 -> 1..1; profile: must-support False -> True
- F-058 `ExplanationOfBenefit.benefitBalance.category`: value set http://hl7.org/fhir/ValueSet/benefit-category -> http://hl7.org/fhir/ValueSet/ex-benefitcategory
- F-059 `ExplanationOfBenefit.benefitBalance.financial.type`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-benefit-type -> http://hl7.org/fhir/ValueSet/benefit-type
- F-066 `ExplanationOfBenefit.careTeam.provider`: reference targets Organization|Practitioner -> Organization|Practitioner|PractitionerRole
- F-068 `ExplanationOfBenefit.careTeam.role`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-claim-careteamrole -> http://hl7.org/fhir/us/carin-bb/ValueSet/C4BBClaimInstitutionalCareTeamRole; profile: binding strength example -> required
- F-069 `ExplanationOfBenefit.careTeam.sequence`: profile: must-support True -> False
- F-072 `ExplanationOfBenefit.diagnosis.diagnosis[x]`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-icd-10 -> http://hl7.org/fhir/us/carin-bb/ValueSet/CDCICD910CMDiagnosisCodes; profile: binding strength example -> required; profile: must-support False -> True
- F-074 `ExplanationOfBenefit.diagnosis.type`: profile: cardinality 0..* -> 1..*; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-ex-diagnosistype -> http://hl7.org/fhir/us/carin-bb/ValueSet/C4BBClaimInpatientInstitutionalDiagnosisType; profile: binding strength example -> required; profile: must-support False -> True
- F-079 `ExplanationOfBenefit.insurance.coverage`: cardinality 0..1 -> 1..1
- F-080 `ExplanationOfBenefit.insurer`: cardinality 0..1 -> 1..1; profile: must-support False -> True
- F-103 `ExplanationOfBenefit.item.revenue`: profile: cardinality 0..1 -> 1..1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-ex-revenue-center -> http://hl7.org/fhir/us/carin-bb/ValueSet/AHANUBCRevenueCodes; profile: binding strength example -> required; profile: must-support False -> True
- F-106 `ExplanationOfBenefit.outcome`: type CodeableConcept -> code; cardinality 0..1 -> 1..1; value set version http://hl7.org/fhir/ValueSet/remittance-outcome -> http://hl7.org/fhir/ValueSet/remittance-outcome|4.0.1; binding strength example -> required; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-remittance-outcome -> http://hl7.org/fhir/ValueSet/remittance-outcome|4.0.1; profile: must-support False -> True
- F-109 `ExplanationOfBenefit.payee.party`: reference targets Organization|Patient|Practitioner|RelatedPerson -> Organization|Patient|Practitioner|PractitionerRole|RelatedPerson; profile: cardinality 0..1 -> 1..1; profile: must-support False -> True
- F-110 `ExplanationOfBenefit.payee.type`: profile: cardinality 0..1 -> 1..1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-payeetype -> http://hl7.org/fhir/us/carin-bb/ValueSet/C4BBPayeeType; profile: binding strength example -> required; profile: must-support False -> True
- F-118 `ExplanationOfBenefit.procedure.procedure[x]`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-icd-10-procedures -> http://hl7.org/fhir/us/carin-bb/ValueSet/CMSICD910PCSProcedureCodes; profile: binding strength example -> required; profile: must-support False -> True
- F-121 `ExplanationOfBenefit.provider`: cardinality 0..1 -> 1..1; reference targets Practitioner -> Organization|Practitioner|PractitionerRole; profile: must-support False -> True
- F-124 `ExplanationOfBenefit.related.reference`: profile: cardinality 0..1 -> 1..1; profile: must-support False -> True
- F-125 `ExplanationOfBenefit.related.relationship`: profile: cardinality 0..1 -> 1..1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-related-claim-relationship -> http://hl7.org/fhir/us/carin-bb/ValueSet/C4BBRelatedClaimRelationshipCodes; profile: binding strength example -> required; profile: must-support False -> True
- F-139 `Patient.link.type`: value set version http://hl7.org/fhir/ValueSet/link-type -> http://hl7.org/fhir/ValueSet/link-type|4.0.1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-link-type -> http://hl7.org/fhir/ValueSet/link-type|4.0.1
- F-142 `Coverage?_profile`: search parameter new in v2
- F-143 `Patient?_has:Coverage.extension`: search parameter new in v2
- F-144 `Patient?_has:Coverage.rfrncyr`: search parameter new in v2

## UNVERIFIABLE: a human must check (10)

Headers and policies are not in any specification. Each needs a person to confirm it.

- **data window** (docs/v1/blue-button-v1-stu3-docs.md:29, LOW): Enables a beneficiary to grant an application access to four years of their Part A, B, and D claims data
- **Content-Encoding** (docs/v1/blue-button-v1-stu3-docs.md:572, MEDIUM): Therefore, developers should ensure their applications handle this scenario gracefully by checking for the **Content-Encoding: gzip** response header before try
- **policy document** (docs/v1/blue-button-v1-stu3-docs.md:813, LOW): Please be responsible with your API usage and comply with the Service Management Rights to Limit conditions in the Blue Button 2.0 API Terms of Service.
- **policy document** (docs/v1/blue-button-v1-stu3-docs.md:916, LOW): In order to gain production access, an organization should start by reviewing the [Terms of Service](/terms/), [production access user guide](/guide/), and [che
- **policy document** (docs/v1/blue-button-v1-stu3-docs.md:916, LOW): Once an organization believes it is fulfilling all the requirements detailed in the checklist and is adherent to the terms of service, they should email [bluebu
- **policy document** (docs/v1/blue-button-v1-stu3-docs.md:924, LOW): **Your Privacy Policy**
- **policy document** (docs/v1/blue-button-v1-stu3-docs.md:926, LOW): You will be asked to provide a URL to your privacy policy and terms and conditions when registering your app in the Blue Button 2.0 API Developer Portal.
- **rate limit** (docs/v1/blue-button-v1-stu3-docs.md:928, LOW): **Rate Limiting and Data Refresh**
- **policy document** (docs/v1/terms-v1.md:11, LOW): This document is intended for reference only as applications transition to our new terms of service.
- **policy document** (docs/v1/terms-v1.md:13, LOW): View the [current terms of service](/terms/).

## Appendix: LOW items by resource

### Coverage (3)

- F-019 MISSING `Coverage.subrogation`: new in v2
- F-048 MISSING `Coverage.identifier`: profile: must-support False -> True
- F-050 MISSING `Coverage.period`: profile: must-support False -> True

### ExplanationOfBenefit (75)

- F-004 MISSING `ExplanationOfBenefit.item.informationSequence`: informationLinkId was renamed informationSequence (HL7 R3-R4 map)
- F-005 MISSING `ExplanationOfBenefit.item.procedureSequence`: procedureLinkId was renamed procedureSequence (HL7 R3-R4 map)
- F-009 MISSING `ExplanationOfBenefit.addItem.itemSequence`: sequenceLinkId may have become itemSequence (similarity 0.715)
- F-013 MISSING `ExplanationOfBenefit.adjudication`: organization may have become adjudication (similarity 0.583)
- F-014 MISSING `ExplanationOfBenefit.addItem.detail.factor`: category may have become factor (similarity 0.571)
- F-015 MISSING `ExplanationOfBenefit.addItem.factor`: category may have become factor (similarity 0.571)
- F-020 MISSING `ExplanationOfBenefit.addItem.bodySite`: new in v2
- F-021 MISSING `ExplanationOfBenefit.addItem.detail.net`: new in v2
- F-022 MISSING `ExplanationOfBenefit.addItem.detail.quantity`: new in v2
- F-024 MISSING `ExplanationOfBenefit.addItem.detail.unitPrice`: new in v2
- F-025 MISSING `ExplanationOfBenefit.addItem.detailSequence`: new in v2
- F-026 MISSING `ExplanationOfBenefit.addItem.location[x]`: new in v2
- F-027 MISSING `ExplanationOfBenefit.addItem.net`: new in v2
- F-029 MISSING `ExplanationOfBenefit.addItem.programCode`: new in v2
- F-030 MISSING `ExplanationOfBenefit.addItem.provider`: new in v2
- F-031 MISSING `ExplanationOfBenefit.addItem.quantity`: new in v2
- F-032 MISSING `ExplanationOfBenefit.addItem.subDetailSequence`: new in v2
- F-033 MISSING `ExplanationOfBenefit.addItem.subSite`: new in v2
- F-034 MISSING `ExplanationOfBenefit.addItem.unitPrice`: new in v2
- F-035 MISSING `ExplanationOfBenefit.benefitPeriod`: new in v2
- F-036 MISSING `ExplanationOfBenefit.diagnosis.onAdmission`: new in v2
- F-037 MISSING `ExplanationOfBenefit.formCode`: new in v2
- F-038 MISSING `ExplanationOfBenefit.fundsReserve`: new in v2
- F-039 MISSING `ExplanationOfBenefit.fundsReserveRequested`: new in v2
- F-041 MISSING `ExplanationOfBenefit.preAuthRef`: new in v2
- F-042 MISSING `ExplanationOfBenefit.preAuthRefPeriod`: new in v2
- F-043 MISSING `ExplanationOfBenefit.priority`: new in v2
- F-045 MISSING `ExplanationOfBenefit.procedure.udi`: new in v2
- F-055 MISSING `ExplanationOfBenefit.accident.type`: value set http://hl7.org/fhir/ValueSet/v3-ActIncidentCode -> http://terminology.hl7.org/ValueSet/v3-ActIncidentCode; binding strength required -> extensible
- F-056 MISSING `ExplanationOfBenefit.addItem.detail.modifier`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-claim-modifiers -> http://hl7.org/fhir/ValueSet/claim-modifiers
- F-057 MISSING `ExplanationOfBenefit.addItem.modifier`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-claim-modifiers -> http://hl7.org/fhir/ValueSet/claim-modifiers
- F-060 MISSING `ExplanationOfBenefit.benefitBalance.financial.used[x]`: profile: cardinality 1..1 -> 0..1
- F-061 MISSING `ExplanationOfBenefit.benefitBalance.network`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-benefit-network -> http://hl7.org/fhir/ValueSet/benefit-network
- F-062 MISSING `ExplanationOfBenefit.benefitBalance.term`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-benefit-term -> http://hl7.org/fhir/ValueSet/benefit-term
- F-063 MISSING `ExplanationOfBenefit.benefitBalance.unit`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-benefit-unit -> http://hl7.org/fhir/ValueSet/benefit-unit
- F-064 NEEDS_NOTE `ExplanationOfBenefit.billablePeriod`: profile: must-support False -> True
- F-065 NEEDS_NOTE `ExplanationOfBenefit.careTeam`: profile: cardinality 1..* -> 0..*
- F-067 MISSING `ExplanationOfBenefit.careTeam.qualification`: profile: cardinality 1..1 -> 0..1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-provider-qualification -> http://hl7.org/fhir/ValueSet/provider-qualification; profile: must-support False -> True
- F-073 MISSING `ExplanationOfBenefit.diagnosis.packageCode`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-ex-diagnosisrelatedgroup -> http://hl7.org/fhir/ValueSet/ex-diagnosisrelatedgroup
- F-075 NEEDS_NOTE `ExplanationOfBenefit.disposition`: profile: cardinality 1..1 -> 0..1; profile: must-support True -> False
- F-076 MISSING `ExplanationOfBenefit.enterer`: reference targets Practitioner -> Practitioner|PractitionerRole
- F-077 MISSING `ExplanationOfBenefit.form`: type CodeableConcept -> Attachment; value set http://hl7.org/fhir/ValueSet/forms -> (none); binding strength example -> (none)
- F-081 NEEDS_NOTE `ExplanationOfBenefit.item`: profile: cardinality 1..* -> 0..*
- F-082 NEEDS_NOTE `ExplanationOfBenefit.item.adjudication`: profile: cardinality 1..* -> 2..*; profile: slicing 'none' -> 'sliced by pattern:category; required slices: adjudicationamounttype, inoutnetwork'
- F-083 MISSING `ExplanationOfBenefit.item.adjudication.amount`: profile: cardinality 1..1 -> 0..1; profile: must-support True -> False
- F-086 MISSING `ExplanationOfBenefit.item.bodySite`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-tooth -> http://hl7.org/fhir/ValueSet/tooth
- F-088 MISSING `ExplanationOfBenefit.item.detail`: profile: cardinality 1..* -> 0..*
- F-089 MISSING `ExplanationOfBenefit.item.detail.category`: value set http://hl7.org/fhir/ValueSet/benefit-subcategory -> http://hl7.org/fhir/ValueSet/ex-benefitcategory
- F-090 MISSING `ExplanationOfBenefit.item.detail.modifier`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-claim-modifiers -> http://hl7.org/fhir/ValueSet/claim-modifiers
- F-091 MISSING `ExplanationOfBenefit.item.detail.programCode`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-ex-program-code -> http://hl7.org/fhir/ValueSet/ex-program-code
- F-092 MISSING `ExplanationOfBenefit.item.detail.quantity`: profile: must-support False -> True
- F-093 MISSING `ExplanationOfBenefit.item.detail.revenue`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-ex-revenue-center -> http://hl7.org/fhir/ValueSet/ex-revenue-center
- F-094 MISSING `ExplanationOfBenefit.item.detail.subDetail.category`: value set http://hl7.org/fhir/ValueSet/benefit-subcategory -> http://hl7.org/fhir/ValueSet/ex-benefitcategory
- F-095 MISSING `ExplanationOfBenefit.item.detail.subDetail.modifier`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-claim-modifiers -> http://hl7.org/fhir/ValueSet/claim-modifiers
- F-096 MISSING `ExplanationOfBenefit.item.detail.subDetail.programCode`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-ex-program-code -> http://hl7.org/fhir/ValueSet/ex-program-code
- F-097 MISSING `ExplanationOfBenefit.item.detail.subDetail.revenue`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-ex-revenue-center -> http://hl7.org/fhir/ValueSet/ex-revenue-center
- F-098 NEEDS_NOTE `ExplanationOfBenefit.item.location[x]`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-service-place -> http://hl7.org/fhir/ValueSet/service-place; profile: slicing 'sliced by ?' -> 'none'
- F-099 NEEDS_NOTE `ExplanationOfBenefit.item.modifier`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-claim-modifiers -> http://hl7.org/fhir/us/carin-bb/ValueSet/AMACPTCMSHCPCSModifiers; profile: binding strength example -> required; profile: must-support False -> True
- F-100 MISSING `ExplanationOfBenefit.item.noteNumber`: profile: must-support False -> True
- F-101 MISSING `ExplanationOfBenefit.item.programCode`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-ex-program-code -> http://hl7.org/fhir/ValueSet/ex-program-code
- F-102 NEEDS_NOTE `ExplanationOfBenefit.item.quantity`: profile: cardinality 1..1 -> 0..1
- F-104 NEEDS_NOTE `ExplanationOfBenefit.item.serviced[x]`: profile: cardinality 1..1 -> 0..1; profile: slicing 'sliced by ?' -> 'sliced by type:$this'
- F-105 MISSING `ExplanationOfBenefit.item.subSite`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-surface -> http://hl7.org/fhir/ValueSet/surface
- F-108 MISSING `ExplanationOfBenefit.payee`: profile: must-support False -> True
- F-111 NEEDS_NOTE `ExplanationOfBenefit.payment`: profile: cardinality 1..1 -> 0..1; profile: must-support False -> True
- F-112 MISSING `ExplanationOfBenefit.payment.adjustmentReason`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-payment-adjustment-reason -> http://hl7.org/fhir/ValueSet/payment-adjustment-reason
- F-113 MISSING `ExplanationOfBenefit.payment.amount`: profile: cardinality 1..1 -> 0..1
- F-114 MISSING `ExplanationOfBenefit.payment.date`: profile: cardinality 1..1 -> 0..1
- F-115 MISSING `ExplanationOfBenefit.payment.type`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-ex-paymenttype -> http://hl7.org/fhir/us/carin-bb/ValueSet/C4BBPayerClaimPaymentStatusCode; profile: binding strength example -> required; profile: must-support False -> True
- F-116 MISSING `ExplanationOfBenefit.procedure`: profile: must-support False -> True
- F-117 MISSING `ExplanationOfBenefit.procedure.date`: profile: must-support False -> True
- F-119 MISSING `ExplanationOfBenefit.processNote`: profile: must-support False -> True
- F-120 MISSING `ExplanationOfBenefit.processNote.type`: type CodeableConcept -> code; value set version http://hl7.org/fhir/ValueSet/note-type -> http://hl7.org/fhir/ValueSet/note-type|4.0.1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-note-type -> http://hl7.org/fhir/ValueSet/note-type|4.0.1
- F-123 MISSING `ExplanationOfBenefit.related`: profile: must-support False -> True
- F-127 MISSING `ExplanationOfBenefit.subType`: cardinality 0..* -> 0..1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-claim-subtype -> http://hl7.org/fhir/ValueSet/claim-subtype

### Patient (8)

- F-129 MISSING `Patient.active`: fixed/default value defaultValueBoolean=true -> (none)
- F-132 MISSING `Patient.communication`: profile: must-support False -> True
- F-133 MISSING `Patient.contact.gender`: value set version http://hl7.org/fhir/ValueSet/administrative-gender -> http://hl7.org/fhir/ValueSet/administrative-gender|4.0.1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-administrative-gender -> http://hl7.org/fhir/ValueSet/administrative-gender|4.0.1
- F-134 MISSING `Patient.contact.relationship`: value set http://hl7.org/fhir/ValueSet/v2-0131 -> http://hl7.org/fhir/ValueSet/patient-contactrelationship
- F-135 MISSING `Patient.deceased[x]`: profile: must-support False -> True; profile: slicing 'none' -> 'sliced by type:$this'
- F-137 MISSING `Patient.generalPractitioner`: reference targets Organization|Practitioner -> Organization|Practitioner|PractitionerRole
- F-140 MISSING `Patient.maritalStatus`: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-marital-status -> http://hl7.org/fhir/ValueSet/marital-status
- F-141 MISSING `Patient.telecom`: profile: must-support False -> True


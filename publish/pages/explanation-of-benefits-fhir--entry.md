---
id: "explanation-of-benefits-fhir--entry"
title: "Entry"
api_version: "2 (FHIR R4)"
verified_on: 2026-11-25
source:
  file: "docs/v1/explanation-of-benefits-fhir.md"
  sha256: "23526776152dfdf64d8b84efbf54c5aed4fd3bd6eaf5e3a1f959f705681bef63"
  lines: "50-101"
spec_hashes:
  R4-coverage.json: "a0f97e7bb1109648dbb9305a170aa1e11de40a8bb793e52079b87d51b4fad962"
  R4-explanationofbenefit.json: "493b5d4e25352bdafa7703b1e552840e49ad4c2b27e7f7d32b47465bbf6f687e"
  R4-patient.json: "c60e7a581b7b311d37b4baf0edb87183f3f41242ee3ad8d7fffd3ce79f0a5458"
  STU3-coverage.json: "48690c85cc2e4d188e19ac04ae3b9f99a1ec35f9a333a40abe7447315c7d7a4e"
  STU3-explanationofbenefit.json: "1baa1b00ff7b16bf0347dfe26deaed4f294570dc262975e77b5d4a4992a1db26"
  STU3-patient.json: "785809db7242f260ea1a8bf967eae6b9f05e914f971f150ec7e29e0fb94a6191"
truthlayer_version: "0.1.0"
fixes_applied: 8
open_findings: 4
status: "needs_review"
---
> **Not fully verified:** 4 finding(s) on this section are still open (F-064, F-081, F-107, F-145). See reports/drift-report.md.

## Entry

Each Entry in the Bundle contains an Explanation of Benefit ("claim") and can be thousands of lines long.

<pre>
"entry": [
{
"fullUrl": "https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit/carrier-22011027731",
"resource": {
"resourceType": "ExplanationOfBenefit",
"id": "carrier-22011027731",
"contained": [
{
"resourceType": "ReferralRequest",
"id": "1",
"status": "completed",
"subject": {
"reference": "Patient/20140000008325"
},
"requester": {
"agent": {
"identifier": {
"system": "http://hl7.org/fhir/sid/us-npi",
"value": "999999999999"
}
}
},
&#10;... and thousands of lines of additional data...
&#10;</pre>

You will find these FHIR resources in the Entry:

- resourceType
- id
- contained
- extension
- identifier
status (v2 note: cardinality 0..1 -> 1..1; value set version http://hl7.org/fhir/ValueSet/explanationofbenefit-status -> http://hl7.org/fhir/ValueSet/explanationofbenefit-status|4.0.1; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-explanationofbenefit-status -> http://hl7.org/fhir/ValueSet/explanationofbenefit-status|4.0.1)
type (v2 note: cardinality 0..1 -> 1..1; binding strength required -> extensible; profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-claim-type -> http://hl7.org/fhir/ValueSet/claim-type; profile: fixed/default value (none) -> patternCodeableConcept={"coding": [{"code": "institutional", "system": "http://terminology.hl7.org/CodeSystem/claim-type"}]})
- patient
- billableperiod
referral (v2 note: reference targets ReferralRequest -> ServiceRequest)
disposition (v2 note: profile: cardinality 1..1 -> 0..1; profile: must-support True -> False)
careTeam (v2 note: profile: cardinality 1..* -> 0..*)
diagnosis (v2 note: profile: cardinality 0..* -> 1..*; profile: must-support False -> True)
insurance (v2 note: cardinality 0..1 -> 1..*)
- item
payment (v2 note: profile: cardinality 1..1 -> 0..1; profile: must-support False -> True)
- benefitBalance

[Download a sample Explanation of Benefit Entry](/sample-eob-entry.json)

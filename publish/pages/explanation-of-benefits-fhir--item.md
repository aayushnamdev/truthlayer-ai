---
id: "explanation-of-benefits-fhir--item"
title: "Item"
api_version: "2 (FHIR R4)"
verified_on: 2026-11-25
source:
  file: "docs/v1/explanation-of-benefits-fhir.md"
  sha256: "23526776152dfdf64d8b84efbf54c5aed4fd3bd6eaf5e3a1f959f705681bef63"
  lines: "102-191"
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
> **Not fully verified:** 4 finding(s) on this section are still open (F-006, F-081, F-084, F-085). See reports/drift-report.md.

## Item

The Item resource with the Entry resource contains the bulk of the Explanation of Benefit information including:

- extension
- sequence
careTeamSequence
diagnosisSequence
category (v2 note: value set http://hl7.org/fhir/ValueSet/benefit-subcategory -> http://hl7.org/fhir/ValueSet/ex-benefitcategory)
- service
modifier (v2 note: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-claim-modifiers -> http://hl7.org/fhir/us/carin-bb/ValueSet/AMACPTCMSHCPCSModifiers; profile: binding strength example -> required; profile: must-support False -> True)
servicedPeriod (v2 note: profile: cardinality 1..1 -> 0..1; profile: slicing 'sliced by ?' -> 'sliced by type:$this')
locationCodeableConcept (v2 note: profile: value set https://bluebutton.cms.gov/assets/ig/ValueSet-service-place -> http://hl7.org/fhir/ValueSet/service-place; profile: slicing 'sliced by ?' -> 'none')
quantity (v2 note: profile: cardinality 1..1 -> 0..1)
adjudication (v2 note: profile: cardinality 1..* -> 2..*; profile: slicing 'none' -> 'sliced by pattern:category; required slices: adjudicationamounttype, inoutnetwork')

You will see the Extension FHIR resource with CMS specific coding systems as well as common industry coding systems.

<pre>
"item": [
{
"extension": [
{
"url": "http://hl7.org/fhir/ValueSet/v3-ActInvoiceGroupCode",
"valueCoding": {
"system": "http://hl7.org/fhir/ValueSet/v3-ActInvoiceGroupCode",
"code": "CSPINV"
}
},
{
"url": "https://bluebutton.cms.gov/resources/variables/carr_line_mtus_cd",
"valueCoding": {
"system": "https://bluebutton.cms.gov/resources/variables/carr_line_mtus_cd",
"code": "3",
"display": "Services"
}
},
</pre>

Most of the output follows a similar pattern. Here you see the Category FHIR resource with a system, code and display value.

<pre>
"category": {
"coding": [
{
"system": "https://bluebutton.cms.gov/resources/variables/line_cms_type_srvc_cd",
"code": "1",
"display": "Medical care"
}
]
}
</pre>

The Adjudication resource contains a depth of financial information about the claim processing.

<pre>
"adjudication": [
{
"category": {
"coding": [
{
"system": "CMS Adjudications",
"code": "https://bluebutton.cms.gov/resources/variables/carr_line_rdcd_pmt_phys_astn_c",
"display": "Carrier Line Reduced Payment Physician Assistant Code"
}
]
},
"reason": {
"coding": [
{
"system": "https://bluebutton.cms.gov/resources/variables/carr_line_rdcd_pmt_phys_astn_c",
"code": "0",
"display": "N/A"
}
]
}
},
{
"extension": [
{
"url": "https://bluebutton.cms.gov/resources/variables/line_pmt_80_100_cd",
"valueCoding": {
"system": "https://bluebutton.cms.gov/resources/variables/line_pmt_80_100_cd",
"code": "0",
"display": "80%"
}
}
]
&#10;</pre>

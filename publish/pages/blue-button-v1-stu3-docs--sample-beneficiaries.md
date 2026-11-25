---
id: "blue-button-v1-stu3-docs--sample-beneficiaries"
title: "Sample Beneficiaries"
api_version: "2 (FHIR R4)"
verified_on: 2026-11-25
source:
  file: "docs/v1/blue-button-v1-stu3-docs.md"
  sha256: "30976f71442d0b15c92ef5e77a151b40e64d74fbf7fb41ad93793b299fa37f69"
  lines: "833-913"
spec_hashes:
  R4-coverage.json: "a0f97e7bb1109648dbb9305a170aa1e11de40a8bb793e52079b87d51b4fad962"
  R4-explanationofbenefit.json: "493b5d4e25352bdafa7703b1e552840e49ad4c2b27e7f7d32b47465bbf6f687e"
  R4-patient.json: "c60e7a581b7b311d37b4baf0edb87183f3f41242ee3ad8d7fffd3ce79f0a5458"
  STU3-coverage.json: "48690c85cc2e4d188e19ac04ae3b9f99a1ec35f9a333a40abe7447315c7d7a4e"
  STU3-explanationofbenefit.json: "1baa1b00ff7b16bf0347dfe26deaed4f294570dc262975e77b5d4a4992a1db26"
  STU3-patient.json: "785809db7242f260ea1a8bf967eae6b9f05e914f971f150ec7e29e0fb94a6191"
truthlayer_version: "0.1.0"
fixes_applied: 0
open_findings: 3
status: "needs_review"
---
> **Not fully verified:** 3 finding(s) on this section are still open (F-006, F-008, F-081). See reports/drift-report.md.

## Sample Beneficiaries

[CSV of 100 sample beneficiaries with rich claims data](/synthetic_users_by_claim_count_full.csv)

When getting started with the Blue Button 2.0 API, it can be overwhelming to understand all of the coding systems and types of data that can be found in the Explanation of Benefit FHIR resource.

Below are some hypothetical Beneficiaries that gives you a sense of what is found in claims data.

**Meet Lucille**

Lucille is an 70-year old female. She has non-small cell lung cancer. Prior to her diagnosis, Lucille was active and had no significant health issues. She went on daily walks around her neighborhood, did yoga and made a concerted effort to eat healthy. Lucille smoked cigarettes for a few years when she was a teenager, but quit after her father passed away from lung cancer. Her only other family history is mild hypertension on her mother’s side.

Below are some examples you may find in the Explanation of Benefit FHIR resource for Lucille.

Office Visit

<pre>
<code>
"service": {
"coding": [{
"system": "https://www.cms.gov/Medicare/Coding/MedHCPCSGenInfo/index.html",
"version": "0",
"code": "99215"
</code>
</pre>

Lung Biopsy

<pre>
<code>
"procedureCodeableConcept": {
"coding": [{
"system": "http://hl7.org/fhir/sid/icd-9-cm",
"code": "3328"
</code>
</pre>

Diagnostic Radiology

<pre>
<code>
"service": {
"coding": [{
"system": "https://www.cms.gov/Medicare/Coding/MedHCPCSGenInfo/index.html",
"version": "0",
"code": "70553"
</code>
</pre>

Radiation Therapy

<pre>
<code>
"service": {
"coding": [{
"system": "https://www.cms.gov/Medicare/Coding/MedHCPCSGenInfo/index.html",
"version": "9",
"code": "77263"
</code>
</pre>

Chemo

<pre>
<code>
"service": {
"coding": [{
"system": "https://www.cms.gov/Medicare/Coding/MedHCPCSGenInfo/index.html",
"version": "0",
"code": "96400"
</code>
</pre>

**Meet Jack**

"Jack" is a hypothetical 70 year-old male with Type 2 Diabetes and high blood pressure. Jack takes daily medication and his Doctor told him he needs to lose weight. He takes Glimepiride to help control his blood sugar and previously was on Metformin.

[Learn more about "Jack" (PDF)](https://cmsgov.github.io/bluebutton-developer-help/Jack-Persona.pdf)

------------------------------------------------------------------------

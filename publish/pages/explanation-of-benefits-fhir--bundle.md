---
id: "explanation-of-benefits-fhir--bundle"
title: "Bundle"
api_version: "2 (FHIR R4)"
verified_on: 2026-11-25
source:
  file: "docs/v1/explanation-of-benefits-fhir.md"
  sha256: "23526776152dfdf64d8b84efbf54c5aed4fd3bd6eaf5e3a1f959f705681bef63"
  lines: "13-28"
spec_hashes:
  R4-coverage.json: "a0f97e7bb1109648dbb9305a170aa1e11de40a8bb793e52079b87d51b4fad962"
  R4-explanationofbenefit.json: "493b5d4e25352bdafa7703b1e552840e49ad4c2b27e7f7d32b47465bbf6f687e"
  R4-patient.json: "c60e7a581b7b311d37b4baf0edb87183f3f41242ee3ad8d7fffd3ce79f0a5458"
  STU3-coverage.json: "48690c85cc2e4d188e19ac04ae3b9f99a1ec35f9a333a40abe7447315c7d7a4e"
  STU3-explanationofbenefit.json: "1baa1b00ff7b16bf0347dfe26deaed4f294570dc262975e77b5d4a4992a1db26"
  STU3-patient.json: "785809db7242f260ea1a8bf967eae6b9f05e914f971f150ec7e29e0fb94a6191"
truthlayer_version: "0.1.0"
fixes_applied: 1
open_findings: 0
status: "verified"
---
## Bundle

In FHIR, a [Bundle](https://www.hl7.org/fhir/bundle-definitions.html) is a collection of resources. You will see type, total and more specified for the Bundle.

<pre>
"resourceType": "Bundle",
"id": "13ea5887-2d4b-437e-80e5-3c18b6e6e185",
"meta": {
"lastUpdated": "2018-02-22T23:35:27.878-05:00"
}
</pre>

Within each entry, you will find additional resourceTypes such as "Observation" or "ReferralRequest" that classifies the entry. Each entry will have information like "Code" and "valueQuantity". Resources have many ResourceTypes such as ReferralRequest, Observation, etc. (removed in v2)

------------------------------------------------------------------------

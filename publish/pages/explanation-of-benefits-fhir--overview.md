---
id: "explanation-of-benefits-fhir--overview"
title: "Overview"
api_version: "2 (FHIR R4)"
verified_on: 2026-11-25
source:
  file: "docs/v1/explanation-of-benefits-fhir.md"
  sha256: "23526776152dfdf64d8b84efbf54c5aed4fd3bd6eaf5e3a1f959f705681bef63"
  lines: "7-12"
spec_hashes:
  R4-coverage.json: "a0f97e7bb1109648dbb9305a170aa1e11de40a8bb793e52079b87d51b4fad962"
  R4-explanationofbenefit.json: "493b5d4e25352bdafa7703b1e552840e49ad4c2b27e7f7d32b47465bbf6f687e"
  R4-patient.json: "c60e7a581b7b311d37b4baf0edb87183f3f41242ee3ad8d7fffd3ce79f0a5458"
  STU3-coverage.json: "48690c85cc2e4d188e19ac04ae3b9f99a1ec35f9a333a40abe7447315c7d7a4e"
  STU3-explanationofbenefit.json: "1baa1b00ff7b16bf0347dfe26deaed4f294570dc262975e77b5d4a4992a1db26"
  STU3-patient.json: "785809db7242f260ea1a8bf967eae6b9f05e914f971f150ec7e29e0fb94a6191"
truthlayer_version: "0.1.0"
fixes_applied: 0
open_findings: 0
status: "verified"
---
## Overview

The [ExplanationOfBenefit FHIR Resource](https://www.hl7.org/fhir/explanationofbenefit.html) is how the Blue Button 2.0 API represents the bulk of the beneficiary's data. Each one can be thousands of lines long.

<pre>curl --header "Authorization: Bearer AUTHORIZATION TOKEN"  "https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit/?patient=20140000008325"</pre>

---
id: "blue-button-v1-stu3-docs--fhir-data-model"
title: "FHIR Data Model"
api_version: "2 (FHIR R4)"
verified_on: 2026-11-25
source:
  file: "docs/v1/blue-button-v1-stu3-docs.md"
  sha256: "30976f71442d0b15c92ef5e77a151b40e64d74fbf7fb41ad93793b299fa37f69"
  lines: "783-832"
spec_hashes:
  R4-coverage.json: "a0f97e7bb1109648dbb9305a170aa1e11de40a8bb793e52079b87d51b4fad962"
  R4-explanationofbenefit.json: "493b5d4e25352bdafa7703b1e552840e49ad4c2b27e7f7d32b47465bbf6f687e"
  R4-patient.json: "c60e7a581b7b311d37b4baf0edb87183f3f41242ee3ad8d7fffd3ce79f0a5458"
  STU3-coverage.json: "48690c85cc2e4d188e19ac04ae3b9f99a1ec35f9a333a40abe7447315c7d7a4e"
  STU3-explanationofbenefit.json: "1baa1b00ff7b16bf0347dfe26deaed4f294570dc262975e77b5d4a4992a1db26"
  STU3-patient.json: "785809db7242f260ea1a8bf967eae6b9f05e914f971f150ec7e29e0fb94a6191"
truthlayer_version: "0.1.0"
fixes_applied: 0
open_findings: 1
status: "needs_review"
---
> **Not fully verified:** 1 finding(s) on this section are still open (F-148). See reports/drift-report.md.

## FHIR Data Model

We have mapped over 1,300 fields from the CMS claims data warehouse into FHIR. These fields are surfaced across the Patient, Coverage and Explanation of Benefits FHIR resources.

- Beneficiary Enrollment Record
- Carrier Claims
- Durable Medical Equipment
- Home Health Agency Claims
- Hospice Claims
- Inpatient Claims
- Outpatient Claims
- Part D Events
- Skilled Nursing Facility Claims

The Blue Button 2.0 API FHIR data model leverages coding systems specific to Medicare billing forms and/or the Chronic Conditions Warehouse, FHIR and Industry Coding Systems.

For Example:

- [National Drug Code Directory](https://www.accessdata.fda.gov/scripts/cder/ndc/)
- [HL7 v3 Code System ActCode](http://hl7.org/fhir/v3/ActCode/cs.html)
- [ICD-10](https://hl7.org/fhir/STU3/valueset-icd-10.html)

[View the full list of Blue Button 2.0 API FHIR Data Model Coding Systems and Identifiers](https://github.com/CMSgov/bluebutton-data-server/blob/master/dev/data-model.md)

**How Often Will New/Updated Data Be Available?**

Medicare Part A, B, and D claims data will be refreshed weekly.

Our schedules may vary depending on many things like maintenance, delayed delivery of claims to the CCW data warehouse, or additional data quality processing that's needed.

We recommend you have a daily job to fetch new claims data for your users. Please be responsible with your API usage and comply with the Service Management Rights to Limit conditions in the Blue Button 2.0 API Terms of Service.

**Synthetic Data**

The CMS Blue Button 2.0 API offers a synthetic data set for developers to test against. This means that each request returns a realistic value. For example, if a patient is prescribed the diabetes medication Metformin, the associated cost and date of this prescription will be accurate.

Please note that this synthetic data set does not represent a longitudinal patient view. The claims—though representative independently—are shuffled and randomly assigned to patients. To build the synthetic data set, we selected a number of random claims, and shuffling them like a deck of cards among a group of fictitious Patient IDs. This will allow developers to test the Blue Button 2.0 API system, but could result in a patient with records for contradictory procedures.

**Production Data**

The CMS Blue Button 2.0 API has at least one claim for over 53M beneficiaries.

Today, there are approximately 38M beneficiaries in traditional or fee-for-service Medicare. The Blue Button 2.0 API has Part A/B/D data for those beneficiaries plus Part D data for some beneficiaries on Medicare Advantage plans.

Part D has always been a separate program, but certain plans include both the MA benefits (Part C) and Part D. As a result, Part D drug event data is collected separately from MA encounter data. Part D drug event data for all participants in Part D has been collected by the agency since the program began in the mid-2000s.

The API also has historical claims data going back four years. All of these factors contribute to the 53M number we use to describe the total number of beneficiaries available via the Blue Button 2.0 API.

------------------------------------------------------------------------

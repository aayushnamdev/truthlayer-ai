---
id: "blue-button-v1-stu3-docs--developer-guidelines"
title: "Developer Guidelines"
api_version: "2 (FHIR R4)"
verified_on: 2026-11-25
source:
  file: "docs/v1/blue-button-v1-stu3-docs.md"
  sha256: "30976f71442d0b15c92ef5e77a151b40e64d74fbf7fb41ad93793b299fa37f69"
  lines: "920-949"
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
> **Not fully verified:** 3 finding(s) on this section are still open (F-151, F-152, F-153). See reports/drift-report.md.

## Developer Guidelines

Below are guidelines you should follow to be successful in your Blue Button 2.0 API integration.

**Your Privacy Policy**

You will be asked to provide a URL to your privacy policy and terms and conditions when registering your app in the Blue Button 2.0 API Developer Portal. These links should be easy to access and understand by a beneficiary using your app. Consider using the [Model Privacy Notice](https://www.healthit.gov/topic/privacy-security-and-hipaa/model-privacy-notice-mpn).

**Rate Limiting and Data Refresh**

Medicare Part A, B, and D claims data will be refreshed weekly.

Our schedules may vary depending on many things like maintenance, delayed delivery of claims to the CCW data warehouse, or additional data quality processing that's needed.

We recommend you have a daily or weekly job to fetch new claims data for your users. Please be responsible with your API usage and comply with the Service Management Rights to Limit conditions in the [Blue Button 2.0 API Terms of Service](/terms/).

**Use of the Blue Button 2.0 API Logo**

The Blue Button 2.0 API logo and usage guidelines is detailed [here](https://www.healthit.gov/topic/health-it-initiatives/blue-button/logo-and-usage).

**Beneficiary Revokes Access**

A beneficiary may revoke access to your application via the Medicare website. When you encounter an invalid token indicating a beneficiary has revoked access, you should make a reasonable attempt to handle that case making it easy for the beneficiary to understand what is happening with their Medicare data.

**"Medicare is unable to retrieve your data at this time due to an internal issue. Our team is aware of the issue and is working to resolve it. Please try again at a later time. We apologize for any inconvenience."**

If you or your users encounters this error message, know that our team is aware of the issue and is working to resolve it as quickly as possible.

------------------------------------------------------------------------

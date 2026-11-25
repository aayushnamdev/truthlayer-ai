<!-- SOURCE_URL: https://bluebutton.cms.gov/api-documentation/calling-the-api/ -->
<!-- FETCHED: 2026-11-25 -->
Source: https://bluebutton.cms.gov/api-documentation/calling-the-api/

# Calling the API

This section provides information on basic and common queries against the Blue Button API. For a complete listing of Blue Button API calls, see our [Swagger documentation](https://sandbox.bluebutton.cms.gov/docs/openapi).

## Sandbox vs. Production Environments

### Sandbox

* Available to everyone via test credentials
* Contains test claims data
* Base FHIR URL: `https://sandbox.bluebutton.cms.gov/v2/fhir/`

### Production

* Must [complete the steps](/production-access/) for production credentials
* Contains real Medicare enrollee data
* Base FHIR URL: `https://api.bluebutton.cms.gov/v2/fhir/`

To find enrollees with varying volumes and types of data, use this [CSV of synthetic data](/assets/files/synthetic_users_by_claim_count_full.csv). Using the synthetic data, you can break down claims by type (carrier, inpatient, etc.) for each enrollee/user combination. Synthetic data works in both the Sandbox and Production environments.

## Querying Resources

A listing of common API calls are shown in the table below. See “Base FHIR URLs” above and substitute for as appropriate.

For a complete listing of Blue Button API calls, see our [Swagger documentation](https://sandbox.bluebutton.cms.gov/docs/openapi).

### Patient Resource

Patient resource requests and descriptions

| Request | Description |
| --- | --- |
| `GET {baseURL}/Patient` | Returns a [bundle](https://www.hl7.org/fhir/bundle.html) of [Patient resources](https://www.hl7.org/fhir/patient.html) with one entry (one patient resource). You can use the resource ID `Bundle.entry.resource.id` in later queries. For synthetic data, the ID is a negative number. |
| `GET {baseURL}/Patient/{id}` | Returns a single Patient resource. Replace `{id}` with a valid patient resource ID. See `/Patient` call above. |

### Coverage Resource

Coverage resource requests and descriptions

| Request | Description |
| --- | --- |
| `GET {baseURL}/Coverage` | Returns a [bundle](https://www.hl7.org/fhir/bundle.html) of [Coverage resources](https://www.hl7.org/fhir/coverage.html) |
| `GET {baseURL}/Coverage?beneficiary={id}` | Replace `{id}` with the patient resource ID. Returns a [bundle](https://www.hl7.org/fhir/bundle.html) of [Coverage resources](https://www.hl7.org/fhir/coverage.html) |

### Explanation of Benefit Resource

Explanation of Benefit Resource requests and descriptions

| Request | Description |
| --- | --- |
| `GET {baseURL}/ExplanationOfBenefit` | Returns a [bundle](https://www.hl7.org/fhir/bundle.html) of [Explanation of Benefit resources](https://www.hl7.org/fhir/explanationofbenefit.html). The bundle should contain one or more EOBs. You can use the resource ID located at `Bundle.entry.resource.id` (the explanation of benefit resource ID) in later queries. For synthetic data, the ID is typically formatted as `[claimtype]`–`[number]` Example: `carrier--10114937820` |
| `GET {baseURL}/ExplanationOfBenefit?patient={id}` | Replace `{id}` with patient resource ID. Returns a [bundle](https://www.hl7.org/fhir/bundle.html) of [Explanation of Benefit resources](https://www.hl7.org/fhir/explanationofbenefit.html). The bundle should contain one or more EOBs. You can use the resource ID located at `Bundle.entry.resource.id` (the explanation of benefit resource ID) in later queries. For synthetic data, the ID is typically formatted as `[claimtype]`–`[number]` Example: `carrier--10114937820` |
| `GET {baseURL}/ExplanationOfBenefit/{id}` | Returns a single [Explanation of Benefit resources](https://www.hl7.org/fhir/explanationofbenefit.html). Replace `{id}` with a valid EOB resource ID. See `/ExplanationOfBenefit` call above. |

### Capability Statement Resource

Capability Statement resource requests and descriptions

| Request | Description |
| --- | --- |
| `GET {baseURL}/metadata` | Returns the [FHIR capability statement](https://www.hl7.org/fhir/capabilitystatement.html) (Example: the FHIR features and operations supported by this server) |

### User Info Resource

User Info resource requests and descriptions

| Request | Description |
| --- | --- |
| `GET {host}/{version}/connect/userinfo` | If the user grants access to access to their personal information, `UserInfo` returns name, family name and email. If the user denies access to their personal information, `UserInfo` returns `You do not have permission.` |

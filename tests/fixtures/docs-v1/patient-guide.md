<!-- SYNTHETIC test fixture: invented text, not CMS documentation. API version 1 (FHIR STU3). -->
# Patient guide

This guide describes API version 1 (FHIR STU3) for the invented Example Service.

## Overview

The service returns a patient record. Each patient has a `nickname` and a phoneNumber that apps may show.
Searching works with `?legacy-id=123`. The old workflow also created a ReferralRequest.

## Fields

| Field | Meaning |
|---|---|
| active | Whether the record is active. Optional. |
| birthDate | Date of birth, for example 01/02/2020. |

## GET /v1/fhir/Patient

Returns patients. Send the token in the header.

## Sample

```json
{
  "resourceType": "Patient",
  "maritalStatus": {
    "coding": [ { "code": "M" } ]
  }
}
```

This sample record is synthetic.

## Details

The patient record uses `gender` for the administrative value set and `managingOrganization` to point at the clinic.
Birth dates come from `dob`.
Fetch the `Coverage` resource separately for plan data.
Send the `X-Member-Mode` header to hide names. Access tokens expire after 1 hour.

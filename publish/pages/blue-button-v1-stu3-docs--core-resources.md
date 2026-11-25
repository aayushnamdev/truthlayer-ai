---
id: "blue-button-v1-stu3-docs--core-resources"
title: "Core Resources"
api_version: "2 (FHIR R4)"
verified_on: 2026-11-25
source:
  file: "docs/v1/blue-button-v1-stu3-docs.md"
  sha256: "30976f71442d0b15c92ef5e77a151b40e64d74fbf7fb41ad93793b299fa37f69"
  lines: "381-782"
spec_hashes:
  R4-coverage.json: "a0f97e7bb1109648dbb9305a170aa1e11de40a8bb793e52079b87d51b4fad962"
  R4-explanationofbenefit.json: "493b5d4e25352bdafa7703b1e552840e49ad4c2b27e7f7d32b47465bbf6f687e"
  R4-patient.json: "c60e7a581b7b311d37b4baf0edb87183f3f41242ee3ad8d7fffd3ce79f0a5458"
  STU3-coverage.json: "48690c85cc2e4d188e19ac04ae3b9f99a1ec35f9a333a40abe7447315c7d7a4e"
  STU3-explanationofbenefit.json: "1baa1b00ff7b16bf0347dfe26deaed4f294570dc262975e77b5d4a4992a1db26"
  STU3-patient.json: "785809db7242f260ea1a8bf967eae6b9f05e914f971f150ec7e29e0fb94a6191"
truthlayer_version: "0.1.0"
fixes_applied: 1
open_findings: 7
status: "needs_review"
---
> **Not fully verified:** 7 finding(s) on this section are still open (F-070, F-130, F-131, F-136, F-138, F-145, F-147). See reports/drift-report.md.

## Core Resources

Base Request URL:

<pre>https://sandbox.bluebutton.cms.gov</pre>

### FHIR Resources:

- Explanation of Benefit
- Patient
- Coverage

### UserInfo:

- Get User Profile from an Authorization Token

As a security measure the date of birth, SSN, and HICN will not be provided by the CMS Blue Button 2.0 API.

We use [FHIR Extensions](https://www.hl7.org/fhir/extensibility.html#Extension) in our API responses.

**Explanation of Benefit FHIR Resource**

<pre>/v1/fhir/ExplanationOfBenefit/?patient=[fhir_id]</pre>

The above URL returns all of the beneficiary's Explanation of Benefit (sometimes referred to as an episode of care) records as an [ExplanationOfBenefit FHIR Resource](https://www.hl7.org/fhir/explanationofbenefit.html). The bulk of a beneficiary's data is contained within these ExplanationOfBenefit FHIR resources.  
Each one can be thousands of lines long.

<pre>curl --header "Authorization: Bearer AUTHORIZATION TOKEN"  "https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit/?patient=-20140000008325"</pre>

That API call will return an Explanation of Benefit that contains many FHIR resources and is typically thousands of lines long.

[Learn more about the Explanation of Benefits FHIR resource in the Blue Button 2.0 API](/eob/)

<pre>
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
"reference": "Patient/-20140000008325"
},
"requester": {
"agent": {
"identifier": {
"system": "http://hl7.org/fhir/sid/us-npi",
"value": "999999999999"
}
}
},
"recipient": [
{
"identifier": {
"system": "http://hl7.org/fhir/sid/us-npi",
"value": "999999999999"
}
}
]
}
]
&#10;...this is only a subset of the entire output...
</pre>

**Patient FHIR Resource**

<pre><code>HTTP GET /v1/fhir/Patient/[fhir_id]</code></pre>

The above URL returns the beneficiary's demographics and other administrative information as a [Patient FHIR Resource](https://www.hl7.org/fhir/patient.html). This information is mostly contact information, not medical data.

<pre><code>curl --header "Authorization: Bearer AUTHORIZATION TOKEN"  "https://sandbox.bluebutton.cms.gov/v1/fhir/Patient/-20140000008325"</code></pre>
<pre>
{
"resourceType": "Patient",
"id": "-20140000008325",
"extension": [
{
"url": "https://bluebutton.cms.gov/resources/variables/race",
"valueCoding": {
"system": "https://bluebutton.cms.gov/resources/variables/race",
"code": "1",
"display": "White"
}
}
],
"identifier": [
{
"system": "http://bluebutton.cms.hhs.gov/identifier#bene_id",
"value": "-20140000008325"
},
{
"system": "http://bluebutton.cms.hhs.gov/identifier#hicnHash",
"value": "2025fbc612a884853f0c245e686780bf748e5652360ecd7430575491f4e018c5"
}
],
"name": [
{
"use": "usual",
"family": "Doe",
"given": [
"Jane",
"X"
]
}
],
"gender": "unknown",
"birthDate": "2014-06-01",
"address": [
{
"district": "999",
"state": "15",
"postalCode": "99999"
}
]
}
</pre>

[Download a sample Patient FHIR Resource](/sample-patient-entry.json)

**Coverage FHIR Resource**

<pre>HTTP GET /v1/fhir/Coverage/?beneficiary=[fhir_id]</pre>

The above URL returns the beneficiary's Coverage information as an [Coverage FHIR Resource.](http://hl7.org/fhir/coverage.html)

<pre>curl --header "Authorization: Bearer AUTHORIZATION TOKEN"  "https://sandbox.bluebutton.cms.gov/v1/fhir/Coverage/?beneficiary=-20140000008325"
</pre>
<pre>
<code>
{
"fullUrl": "https://sandbox.bluebutton.cms.gov/v1/fhir/Coverage/part-a-20140000008325",
"resource": {
"resourceType": "Coverage",
"id": "part-a-20140000008325",
"extension": [
{
"url": "https://bluebutton.cms.gov/resources/variables/ms_cd",
"valueCoding": {
"system": "https://bluebutton.cms.gov/resources/variables/ms_cd",
"code": "10",
"display": "Aged without end-stage renal disease (ESRD)"
}
},
{
"url": "https://bluebutton.cms.gov/resources/variables/orec",
"valueCoding": {
"system": "https://bluebutton.cms.gov/resources/variables/orec",
"code": "0",
"display": "Old age and survivor’s insurance (OASI)"
}
},
{
"url": "https://bluebutton.cms.gov/resources/variables/esrd_ind",
"valueCoding": {
"system": "https://bluebutton.cms.gov/resources/variables/esrd_ind",
"code": "0",
"display": "the beneficiary does not have ESRD"
}
},
{
"url": "https://bluebutton.cms.gov/resources/variables/a_trm_cd",
"valueCoding": {
"system": "https://bluebutton.cms.gov/resources/variables/a_trm_cd",
"code": "0",
"display": "Not Terminated"
}
}
]
&#10;...this is only a subset of the entire output...
</code>
</pre>

**Compress Resources for more efficient data transfers**

To improve the performance when transferring large data resources it is possible to turn on compression. Gzip compression is turned off by default. Compression can be activated for the following content types:

- text/html
- text/plain
- application/json
- application/fhir+json

To activate compression add the following to the header:

<pre>
Accept-Encoding: gzip
</pre>

The minimum payload size we will gzip is 1 kilobyte. If the original uncompressed size of the payload is less than 1 kb, we will not apply gzip compression to our response. Therefore, developers should ensure their applications handle this scenario gracefully by checking for the **Content-Encoding: gzip** response header before trying to decompress.

[Download a sample Coverage FHIR Resource](/sample-coverage-entry.json)

**Get User Profile for an Authorization Token**

<pre>HTTP GET /connect/userinfo </pre>

The UserInfo Endpoint is an OAuth 2.0 Protected Resource.The above URL fetches the fictitious beneficiary’s basic account information given an Authorization Token. This is most often used when creating an account within your application. An HTTP GET is called and the response is returned as JSON.

<pre>curl --header "Authorization: Bearer AUTHORIZATION TOKEN" "https://sandbox.bluebutton.cms.gov/v1/connect/userinfo"</pre>
<pre>
{
"sub": "fflinstone",
"prefered_username": "fflinstone",
"given_name": "Fred",
"family_name:, "Flinstone,
"name": "Fred Flinstone",
"email": "pebbles-daddy@example.com",
"created": "2017-11-28",
"patient": {"reference": "Patient/123456789"},
}
</pre>

### More Efficient Data Queries

#### Query by Type

Many developers are interested in specific claim types, such as PDE. The query by type feature will allow applications to request just those claims. This will enable applications to process and download data more quickly and efficiently.

`ExplanationOfBenefit` resources fall into 8 types:

- `CARRIER`
- `DME`
- `HHA`
- `HOSPICE`
- `INPATIENT`
- `OUTPATIENT`
- `PDE`
- `SNF`

By default, the FHIR API returns all of these claim types when requesting the EOB for a beneficiary. You can use the Type query parameter to request specific claim types.

For example, to request only Part D drug claims, add the query parameter:

    ?type=pde

**To request multiple claim types, a list of comma-separated values can be given for the TYPE parameter.**

If multiple codes are specified, EOBs matching all of those claim types will be returned:

    /v1/fhir/ExplanationOfBenefit?patient=123&type=carrier,dme,hha,hospice,inpatient,outpatient,snf

The full list of claim types are:

`carrier`

    https://bluebutton.cms.gov/resources/codesystem/eob-type|carrier

`pde`

    https://bluebutton.cms.gov/resources/codesystem/eob-type|pde

`dme`

    https://bluebutton.cms.gov/resources/codesystem/eob-type|dme

`hha`

    https://bluebutton.cms.gov/resources/codesystem/eob-type|hha

`hospice`

    https://bluebutton.cms.gov/resources/codesystem/eob-type|hospice'

`inpatient`

    https://bluebutton.cms.gov/resources/codesystem/eob-type|inpatient’

`outpatient`

    https://bluebutton.cms.gov/resources/codesystem/eob-type|outpatient’

`snf`

    https://bluebutton.cms.gov/resources/codesystem/eob-type|snf

It is important to use lower case when requesting a claim type. If you submit an invalid combination of claim types or use the wrong case you’ll see a message like this:

    {
        “detail”: “not a valid value”
    }

The status code for this message is a `400 Bad Request`.

### Query by Type Examples:

In the sandbox there are synthetic beneficiaries with three of the eight claim types: - `carrier` - `inpatient` - `pde`

Let us take a synthetic beneficiary record:

Username: **BBUser20023** and Password **PW20023!**

The FHIR ID for this beneficiary is **-20140000000024**

Let us do a regular `ExplanationOfBenefit` request:

    https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit/

This bundle identifies 148 claims, returning the first 10. Here is how the start of the bundle will look:

    {
      “resourceType”: “Bundle”,
      “id”: “9562c9b7-df79-419a-a94b-ef8cc9347e0e”,
      “meta”: {
        “lastUpdated”: “2019-11-05T22:05:48.257-05:00”
      },
    “type”: “searchset”,
    “total”: 148,
    “link”: [
      {
        “relation”: “first”,
        “Url”:    “https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit?_count=10&startIndex=0&patient=-20140000000024”
      },
    …

There are three claim types in this beneficiary’s record: - Carrier (44) - Inpatient (1) - PDE (103)

The queries to request each claim type individually would be:

**Carrier Claims**

    https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit/?type=carrier

Or

    https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit/?type=https://bluebutton.cms.gov/resources/codesystem/eob-type|carrier

**Inpatient Claims**

    https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit/?type=inpatient

Or

    https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit/?type=https://bluebutton.cms.gov/resources/codesystem/eob-type|inpatient

**PDE Claims** Since many of our developers are interested in the Part D drug claims it is now possible to query for only PDE-type claims.

    https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit/?type=pde 

Or

    https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit/?type=https://bluebutton.cms.gov/resources/codesystem/eob-type|pde

#### Query by "lastUpdated" Field

The HL7 FHIR specification provides a [Meta](https://www.hl7.org/fhir/resource.html#Meta) section in each resource. The `lastUpdated` field represents the date and time of the last update. This takes the format of an “instant” type:

    YYYY-MM-DDThh:mm:ss.sss+zz:zz.

The HL7 FHIR specification also provides a `_lastUpdated` query parameter for the search operations on the end-points. By using the `_lastUpdated` query parameter, **an application will be able to request only the records that have changed before or after a specific date**. If you keep track of the date of a previous request, you can request just the changes since your previous request. The format of this request would be:

    https://sandbox.bluebutton.cms.gov/v1/fhir/Patient?_id=-19990000000001&_lastUpdated=gt2020-02-13T08:00:00-05:00&_format=application%2Fjson%2Bfhir’

<div class="ds-c-alert ds-c-alert--hide-icon ds-u-margin-bottom--2">

<div class="ds-c-alert__body">

<h3 class="ds-c-alert__heading">
Note:
</h3>
<p class="ds-c-alert__text">
Do not input dates before 2020-02-12 with <code>\_lastUpdated</code>. Limitations of our backend service prevent data before 2020-02-12 from being tagged correctly.
</p>

</div>

</div>

The output from that request would look like this:

    /v1/fhir/Patient?_id=-19990000000001&_lastUpdated=gt2020-02-13T08:00:00-05:00&_format=application%2Fjson%2Bfhir’
    {
        “resourceType”: “Bundle”,
      “id”: “7d8ff6a1-95f9-4210-b08b-58a96ea74494”,
      “meta”: {
        “lastUpdated”: “2020-02-14T08:57:16.641-05:00”
        },
    “type”: “searchset”,
    “total”: 1,
    “link”: [
      {
        “relation”: “self”,
      “url”: “https://prod-sbx.bfdcloud.net/v1/fhir/Patient?_format=application%2Fjson%2Bfhir&_id=-19990000000001&_lastUpdated=gt2020-02-13T08%3A00%3A00-05%3A00”
      }
    ],
    “entry”: [
      {
        “resource”: {
          “resourceType”: “Patient”,
          “id”: “-19990000000001”,
          “meta”: {
            “lastUpdated”: “2020-02-13T21:53:06.017-05:00”
        },
    “extension”: [
    …

The BB2.0 API supports operators for less than (`lt`), greater than (`gt`), less than or equal (`le`), and greater than or equal (`ge`) the specified instant. It is also possible to specify a time interval by using two `_lastUpdated` parameters like this:

    /v1/fhir/ExplanationOfBenefit?patient=Patient/-19990000000001&_lastUpdated=gt2020-02-13T08:00:00-05:00&_lastUpdated=lt2020-02-14T08:00:00-05:00&_format=application%2Fjson%2Bfhir

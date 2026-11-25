<!-- SOURCE_URL: https://github.com/CMSgov/bluebutton-site-static/blob/f9391f119db329a9d308da8652e7be8a8c4a842a/_pages/eob.md -->
<!-- ORIGINAL_LIVE_URL: https://bluebutton.cms.gov/eob/ (removed from live site) -->
<!-- SNAPSHOT: repo commit f9391f119db329a9d308da8652e7be8a8c4a842a (2023-12-26); file last changed in commit e9055a25 on 2020-10-01 -->
Source: https://github.com/CMSgov/bluebutton-site-static/blob/f9391f119db329a9d308da8652e7be8a8c4a842a/_pages/eob.md
Snapshot: 2023-12-26 (file last changed 2020-10-01)

## Overview

The [ExplanationOfBenefit FHIR Resource](https://www.hl7.org/fhir/explanationofbenefit.html) is how the Blue Button 2.0 API represents the bulk of the beneficiary's data. Each one can be thousands of lines long.

<pre>curl --header "Authorization: Bearer AUTHORIZATION TOKEN"  "https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit/?patient=20140000008325"</pre>

## Bundle

In FHIR, a [Bundle](https://www.hl7.org/fhir/bundle-definitions.html) is a collection of resources. You will see type, total and more specified for the Bundle.

<pre>
"resourceType": "Bundle",
"id": "13ea5887-2d4b-437e-80e5-3c18b6e6e185",
"meta": {
"lastUpdated": "2018-02-22T23:35:27.878-05:00"
}
</pre>

Within each entry, you will find additional resourceTypes such as "Observation" or "ReferralRequest" that classifies the entry. Each entry will have information like "Code" and "valueQuantity". Resources have many ResourceTypes such as ReferralRequest, Observation, etc.

------------------------------------------------------------------------

## Paging

We are using the [link element of the Bundle resource](https://www.hl7.org/fhir/bundle-definitions.html) to handle paging.

<pre>
"link": [
{
"relation": "self",
"url": "https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit/?patient=20140000008325&startIndex=0&count=10"
},
{
"relation": "next",
"url": "https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit/?patient=20140000008325&startIndex=10&count=10"
},
{
"relation": "last",
"url": "https://sandbox.bluebutton.cms.gov/v1/fhir/ExplanationOfBenefit/?patient=20140000008325&startIndex=130&count=10"
}
]
</pre>

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
- status
- type
- patient
- billableperiod
- referral
- disposition
- careTeam
- diagnosis
- insurance
- item
- payment
- benefitBalance

[Download a sample Explanation of Benefit Entry](/sample-eob-entry.json)

## Item

The Item resource with the Entry resource contains the bulk of the Explanation of Benefit information including:

- extension
- sequence
- careTeamLinkId
- diagnosisLinkId
- category
- service
- modifier
- servicedPeriod
- locationCodeableConcept
- quantity
- adjudication

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

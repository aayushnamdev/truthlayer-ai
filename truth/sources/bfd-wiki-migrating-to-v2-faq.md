# Migrating to V2 of our APIs - FAQ

Frequently Asked Questions about the V2 API transition for:

Blue Button 2.0 API (BB2.0)

Beneficiary Claims Data API (BCDA)

Data at the Point of Care (DPC)

Medicare Claims Data to Part D Sponsors API (AB2D)

## What is V2 and how is it different from V1?

BB2.0, BCDA, DPC, and AB2D will each create a version 2 of their APIs (collectively, “V2”).

V2 will conform to the [FHIR R4 specification](https://hl7.org/fhir/R4/) and follow the [CARIN Implementation Guide](http://hl7.org/fhir/us/carin-bb/history.html) for industry alliance. V2 will also make integration and interoperability with all our APIs seamless by enabling them to provide FHIR R4 validated and conformant resources for Patient, Coverage, and Explanation Of Benefits (EOB's). You can [view our RFC](https://github.com/CMSgov/beneficiary-fhir-data/blob/master/docs/rfcs/BFDv2/BFDv2%20RFC.md) on the Beneficiary FHIR Data Server's (BFD) Github repository for more information. (The BFD is a standards-based FHIR API that supports BB2.0, BCDA, DPC, and AB2D.)

In this new version, data about beneficiary claims and coverage will continue to flow smoothly to the partners who rely on it, in alignment with HL7 standards.

> We are currently working on a detailed breakdown of the differences between V1 and V2 for the APIs. We’ll let you know in the Google Group when we publish that information.

## What is FHIR R4? How is it different from R3?

### What is FHIR R4?

FHIR R4 is a normative (stable) release of the standard. Normative releases have gone through a tremendous amount of oversight from the HL7/FHIR community.

If you are curious about the differences between FHIR versions, like “STU3” versus R4, [more information can be found in the FHIR maturity model](https://confluence.hl7.org/display/FHIR/FHIR+Maturity+Model).

### How is it different from FHIR R3?

Because FHIR is a broad standard that covers many different applications, [there is a long list of technical differences between R3 and R4 of FHIR](https://hl7.org/fhir/diff.html), ranging from new fields to changed items to differences in requirements around certain items. It is important to understand that **not all of those changes apply to the BB2.0, BCDA, DPC, or AB2D APIs.**

## Why is CMS creating V2 now?

[*The Interoperability and Patient Access final rule*](https://www.cms.gov/Regulations-and-Guidance/Guidance/Interoperability/index), published May 1, 2020, requires CMS-regulated payers to implement and maintain a secure, standards-based Patient Access API using HL7 FHIR 4.0.1 that allows patients to easily access their claims and encounter information through third-party applications of their choice. In concert with this requirement, CMS is currently developing a V2 of available APIs conformant with FHIR R4.

## What is happening to V1?

We have no plans to remove V1 in the foreseeable future. After V2 is launched in production, we will not add any new features or enhancements to the V1 endpoints. Our support will only cover what is necessary to maintain V1 at its current level of service.

## Why should your product upgrade to V2?

Upgrading to CMS’s V2 API, which is conformant to FHIR R4 and the [*CARIN Alliance Blue Button® Framework and Common Payer Consumer Data Set (CPCDS) IG*](http://hl7.org/fhir/us/carin-bb/history.html), ensures your product is aligned with the latest industry standards. Our V2 API will also be compatible with APIs from many other payers allowing your product to easily serve enrollees for those payers.

Additionally, the V2 API will ensure alignment across HHS interoperability efforts. For instance, if your organization is a CMS-regulated payer you will need to implement your own Patient Access API using FHIR R4 by July 2021. And, all CEHRT users will need to be conformant with FHIR R4 to meet the [ONC regulations](https://www.healthit.gov/curesrule/overview/about-oncs-cures-act-final-rule) on updates to the 2015 CEHRT in the coming years. While V2 will be conformant with FHIR R4, V1 will not be.

Although we will maintain V1 and V2 in parallel for the foreseeable future, after V2 is launched in production, we will stop adding new features or enhancements to the V1 endpoints. Our support for V1 will only cover what is necessary to maintain V1 at its current level of service, meaning any additional fields or feature enhancements will only be added to V2 once it is launched in production.

## How do you test V2 in sandbox?

The first step is to test the V2 data load to make sure it works with your existing application by replacing your existing URL endpoints with the new V2 endpoints when they are available in the sandbox. Send us any feedback about your experience, especially if any breaking changes cause issues in your application. You can provide feedback by emailing <BFD@cms.hhs.gov> or by posting in the BB2.0, BCDA, DPC, or AB2D Google Groups.

## When will V2 be available?

V2 of the APIs will be implemented in summer / fall, 2021. Exact release dates will vary by API. Check your API's Google Group (linked at the bottom of this document) for details.

We are aiming to make V2 available for testing in Sandbox at least two months prior to our production release. Each API will make an announcement in their Google Group when V2 is available to test in the Sandbox.

## Will your V1 access tokens work in V2?

Yes.

## If you switch to V2, will beneficiaries need to reauthorize your BB2.0 application?

No.

## Do you need new credentials for sandbox or production to access V2?

No. You can continue to use your existing credentials once V2 is fully available.

CMS will make select endpoints available in the sandbox ahead of the V2 launch for testing. If you would like to test these endpoints and help us make improvements, please email us at <BFD@cms.hhs.gov>.

## Do you need to revise your privacy policy to switch to V2?

No, you will not need to revise your privacy policy or terms of service when you switch to V2.

As a reminder, if you’re using the Blue Button 2.0 API, any changes you make to your application’s privacy policy or terms of service must be reviewed by the CMS team so you can continue to access the API.

## Are there any breaking changes?

Yes, V2 (FHIR R4) is not backwards compatible with V1 (FHIR R3). A list of technical differences between R3 and R4 of FHIR can be found [here](https://hl7.org/fhir/diff.html).

## Is CMS planning to add any new FHIR resources in V2?

Not at this time. V2 will provide FHIR R4 compatible and CARIN Blue Button CPCDS IG conformant endpoints for our existing resources: Patient, Coverage, and ExplanationofBenefit (EOB).

## Where can you find the latest information?

Join the Google Group for any APIs you access for the most up to date information:

* [Blue Button 2.0 (BB2.0)](https://groups.google.com/g/developer-group-for-cms-blue-button-api)
* [Beneficiary Claims Data API (BCDA)](https://groups.google.com/forum/#!forum/bc-api)
* [Data at the Point of Care (DPC)](https://groups.google.com/forum/#!forum/dpc-api)
* [Medicare Claims Data to Part D Sponsors (AB2D)](https://groups.google.com/g/ab2d-api)

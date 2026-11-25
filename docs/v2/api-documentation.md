<!-- SOURCE_URL: https://bluebutton.cms.gov/api-documentation/ -->
<!-- FETCHED: 2026-11-25 -->
Source: https://bluebutton.cms.gov/api-documentation/

# API Documentation

The Blue Button API enables software developers to build trusted applications, services, and research programs that benefit Medicare enrollees. As a [standards-based API](/api-documentation/#technical-specifications-and-standards), Blue Button provides claims data for more than 64 million people with Medicare.

Blue Button uses [Fast Healthcare Interoperability Resources (FHIR)](https://hl7.org/fhir/R4/overview.html) to share claims data. You can use a variety of tools or client software programs to access the sandbox and production environments.

## Getting started

1. ### Learn about the Blue Button API

   Learn about technical requirements, development environments, and, our process for providing access to enrollee data.
2. ### Create a sandbox account

   Using sandbox credentials, develop and test your Blue Button application using the synthetic data provided.

   [Visit the Sandbox](https://sandbox.bluebutton.cms.gov/v1/accounts/mfa/login)
3. ### Get production access

   Follow the steps on the [Production Access page](/production-access/) to get access to live data in our production environment.

## Technical Specifications and Standards

The Blue Button API is a RESTful API, based on the HL7 FHIR standard and the CARIN Consumer Directed Payer Data Exchange Implementation Guide. It supplies data in JSON format, and uses the OAuth 2.0 protocol for authorization.

* [HL7 FHIR Standard](http://www.hl7.org/fhir/index.html)
* [CARIN Consumer Directed Payer Data Exchange Implementation Guide](http://www.hl7.org/fhir/us/carin-bb/index.html)
* [OAuth 2.0 protocol](https://oauth.net/)
* [RESTful API Overview](https://restfulapi.net/)

## Versions

There are 3 versions of the Blue Button API.

### Version 3

Blue Button Version 3 (v3) is the latest version of the Blue Button API. It’s built on [FHIR Release 4 (R4)](https://hl7.org/fhir/R4/).

v3 has the following improvements:

* Improved claims data timeliness
* Availability of partially adjudicated claims
* Additional Part D information
* Improved FHIR conformance to [C4BB 2.1.0](https://build.fhir.org/ig/HL7/carin-bb/)
* Addition of `StructureDefinition` and `CodeSystem` resources
* Verified FHIR Path for each data element

v3 leverages CMS’ Integrated Data Repository (IDR) as the primary upstream data source, which replaces the Chronic Conditions Warehouse (CCW)-based architecture of v1 and v2.

**Note:** Organizations developing new applications should use v3. v1 and v2 will be deprecated on July 30, 2027. The API Documentation update is in progress and still references v2, but v3 is live in production and testable in sandbox. To read more about how to use v3 check out the [v3 FAQs](/api-documentation/v3-faq/) and [migration guide](/api-documentation/v3-migration-guide/).

### Older Versions

Blue Button Version 2 (v2) is based on [FHIR Release 4 (R4)](https://hl7.org/fhir/R4/) and the [CARIN Consumer Directed Payer Data Exchange (CDPDE) Implementation Guide (CARIN for Blue Button)](https://hl7.org/fhir/us/carin-bb/STU1.1/).

Blue Button Version 1 (v1) is the original Blue Button API, based on [FHIR Release 3 (STU3)](https://hl7.org/fhir/STU3/).

**Note:** Support for v1 and v2 will be deprecated on July 30, 2027.

## Environments

We currently maintain production and sandbox [environments](/api-documentation/calling-the-api/#sandbox-vs-production-environments) for developing with the Blue Button API.

### Sandbox

Develop your application using our sandbox environment. It provides access to synthetic Medicare enrollee data and includes all the same endpoints, resource types, and parameters as production. You can complete all of the same operations in the sandbox as in the production environment.

It’s helpful to know that:

* Sandbox credentials will not work in production.
* While we strive to provide a synthetic data set relevant to most use cases, our synthetic data set is not as comprehensive as production data.

To get started in the developer sandbox, [create an account](https://sandbox.bluebutton.cms.gov/v2/accounts/mfa/login).

### Production

Once your development is nearing completion, get access to live data in our production environment by following the instructions in our [production access user guide](/production-access/). After you complete the requirements in the production access guide and your app is approved, we’ll give you credentials for the production environment.

## Access to Medicare enrollee data

### Scope of access

Applications receive permission to access Medicare enrollee data on a per-user basis. Access to claims data for each individual enrollee begins after they grant access to an application via the Blue Button API’s authorization flow.

Medicare enrollees may always opt to omit personal data such as name, date of birth, race, and sex when granting access to claims data. An enrollee’s choice during the Blue Button authorization flow determines the [scope](/api-documentation/authorization/#scopes) of access an application will have to their data.

### Duration of access

The length of time that an application can continue to pull new claims data from Medicare depends on the application’s use case and category. The Blue Button API team determines your application’s access duration category during the [production access process](/production-access/).

There are 3 categories for data access duration:

Categories for data access duration

| Category | Description and Notes |
| --- | --- |
| 1 hour | One-time use apps (Example: An app that pulls an enrollee’s data once to recommend insurance plans)   * These apps do not usually require separate logins or store users’ data over time. * Authorization will be granted for 1 hour, without the ability to refresh the token. * If an enrollee uses the app more than once outside the 1-hour window, they must reauthorize for each data pull. |
| 13 months | Apps that pull data for the enrollee’s use on an ongoing basis (Example: A personal health aggregator app.)   * Authorization will be granted for 13 months. * For continued access after 13 months, an app must prompt the user to reauthorize. |
| Research | Apps that facilitate Institutional Review Board (IRB)-approved clinical research studies   * Access to an enrollee’s data will never expire unless revoked by the enrollee or by the Blue Button team due to app inactivity over a period of time. * Research apps will be reviewed every 2 years to ensure that they are still active. * If a research app is not active at a 2-year check-in, we will contact the app team for confirmation that they still need Blue Button API access. * If you have a research app, please keep us updated on changes to your contact information and watch for emails from [BlueButtonAPI@cms.hhs.gov](mailto:BlueButtonAPI@cms.hhs.gov). |

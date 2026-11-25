---
id: "blue-button-v1-stu3-docs--authorization"
title: "Authorization"
api_version: "2 (FHIR R4)"
verified_on: 2026-11-25
source:
  file: "docs/v1/blue-button-v1-stu3-docs.md"
  sha256: "30976f71442d0b15c92ef5e77a151b40e64d74fbf7fb41ad93793b299fa37f69"
  lines: "180-380"
spec_hashes:
  R4-coverage.json: "a0f97e7bb1109648dbb9305a170aa1e11de40a8bb793e52079b87d51b4fad962"
  R4-explanationofbenefit.json: "493b5d4e25352bdafa7703b1e552840e49ad4c2b27e7f7d32b47465bbf6f687e"
  R4-patient.json: "c60e7a581b7b311d37b4baf0edb87183f3f41242ee3ad8d7fffd3ce79f0a5458"
  STU3-coverage.json: "48690c85cc2e4d188e19ac04ae3b9f99a1ec35f9a333a40abe7447315c7d7a4e"
  STU3-explanationofbenefit.json: "1baa1b00ff7b16bf0347dfe26deaed4f294570dc262975e77b5d4a4992a1db26"
  STU3-patient.json: "785809db7242f260ea1a8bf967eae6b9f05e914f971f150ec7e29e0fb94a6191"
truthlayer_version: "0.1.0"
fixes_applied: 2
open_findings: 0
status: "verified"
---
## Authorization

To use the Blue Button 2.0 OAuth 2 a developer must [register their application](https://sandbox.bluebutton.cms.gov/v1/o/applications/).

A registered application is given a client ID and a client secret. The secret should only be used if it can be kept confidential, such as communication between your server and the Blue Button 2.0 API. Otherwise the [Client Application Flow](#client-application-flow) may be used.

### Scopes

Access tokens have a scope, which defines what the access token can do and what resources it can access. For our purposes, scopes are primarily utilized to give Medicare beneficiaries more granular choice over what data they would like to share with applications. The Blue Button 2.0 API has implemented [HL7 FHIR Scopes](http://hl7.org/fhir/smart-app-launch/scopes-and-launch-context.html) to manage access to beneficiary data. They look like this:

    patient/Patient.read

    patient/Coverage.read

    patient/ExplanationOfBenefit.read

From the OpenID Connect specification we support:

    profile

This gives access to the `/v1/connect/UserInfo` Endpoint.

Our OAuth screen gives beneficiaries the ability to choose whether or not to share their demographic information. **Your application will need to handle the return of a 403 status code** from the `/v1/fhir/Patient` and `/v1/connect/userinfo` endpoints.

<img style="width: 100%;" src="/assets/img/docs/bene_auth_screen.png" alt="The OAuth screen with a choice for benes to share or withhold certain demographic information" />

If the beneficiary declines to share information that your application needs to function, you may display a message explaining why that information is needed and request reauthorization, or handle the collection of that information elsewhere within your application.

The default selection when a beneficiary reaches the authorization screen will be to share all data, including demographic data, with your application. If a beneficiary makes a selection as to whether or not they want to share demographic data with your application and later decides they want to change that selection, they'll need to be taken through the authorization flow again to make a different choice from the OAuth screen.

#### Ensuring you still get the data you need

Take the time to ensure that you have fallbacks in place if you are unable to access the `patient` or `userinfo` endpoints.

For example, if you are getting the `patient_ID` from the `v1/fhir/Patient` endpoint, we recommend getting that identifier from the initial authorization response, or another resource like `ExplanationOfBenefit` or `Coverage`. (v2 note: cardinality 0..1 -> 1..1)

#### Explanation of needed data to Medicare Beneficiaries

If information limited by a scope is required for your application to properly function and it is not possible to get the information in another endpoint, we recommend providing an explanation about why certain data is needed in your user flow.

For example, if you use demographic information to help beneficiaries autofill tedious data-entry, you might want to explain that benefit before they reach the authorization screen. **It is essential, however, that you give beneficiaries the full picture.** If they do share that data with you for one-time data entry, they should know how long you keep it and if it is used for any other purposes.

#### What if my application doesn't need demographic information from beneficiaries?

As stewards of sensitive data, it is important to adopt the practice of only asking for the data that is needed to perform a service for a beneficiary. As you register or edit an application in our Sandbox, you will see an option to choose whether or not your application needs to collect demographic information from beneficiaries.

If you choose not to collect demographic information, Medicare beneficiaries will see a simplified version of the OAuth screen as they no longer need to choose whether or not they want to share that information.

### Native Mobile App Support

Native Mobile App Support follows the [RFC 8252 - OAuth 2.0 for Native Apps](https://tools.ietf.org/html/rfc8252) authentication flow utilizing the [PKCE](https://tools.ietf.org/html/rfc7636) extension and enables a custom URI scheme redirect.

The implementation of the [RFC 8252](https://tools.ietf.org/html/rfc8252) specification enables developers to build mobile applications without requiring a proxy server to route redirect calls to their mobile app.

The [PKCE](https://tools.ietf.org/html/rfc7636) extension provides a technique for public clients to mitigate the threat of a “man-in-the-middle” attack. This involves creating a secret that is used when exchanging the authorization code to obtain an access token.

[PKCE](https://tools.ietf.org/html/rfc7636) uses a code challenge that is derived from a code-verifier. The standard supports two styles of code challenge: - plain - S256

However, the Blue Button 2.0 API only supports the “S256” style code challenge.

Where the:  

``` python
codechallenge = BASE64URL-ENCODE(SHA256(ASCII(codeverifier)))
```

The following additional parameters and values are sent as part of the OAuth2.0 Authorization Request: - `code_challenge` - `codechallengemethod = “S256”`

More details can be found about this flow on [OAuth.com](https://www.oauth.com/). Check out this link: [Protecting Mobile Apps with PKCE - OAuth 2.0 Servers](https://www.oauth.com/oauth2-servers/pkce/)

### Registering Your App for Mobile App Support

When you register your application in the Blue Button 2.0 API Developer Sandbox, you will want to specify a unique custom URI scheme. This should be a unique value that will not conflict with other custom URI schemes implemented on a user’s mobile device.

We recommend that you define your custom URI scheme using a reverse domain name notation. As we developed our own testing application, we implemented a custom URI scheme of: - `gov.cms.bluebutton.oauthtester`

This equated to an `oauthtester` subdomain for the [bluebutton.cms.gov](bluebutton.cms.gov) domain.

The reverse DNS style custom URI scheme should then be coupled with the re-direct path on the mobile device that will handle the call back from the Blue Button 2.0 API.

For example:

``` python
tld.app.subdomain[.subsubdomain]:/callback/path/endpoint
```

A coding example of an OAuth 2.0 and PKCE flow is available here: [Authorization Code with PKCE Flow - OAuth 2.0 Playground](https://www.oauth.com/playground/authorization-code-with-pkce.html)

The Blue Button 2.0 API engineering team has also created a sample Android application. You can review or fork the code here: <https://github.com/CMSgov/bluebutton-sample-client-android>

### Redirect_URI

When creating an Application in the sandbox a redirect URI is required. This is the API endpoint on *your* system that receives the callback from the Blue Button 2.0 API after a beneficiary is passed to the Blue Button 2.0 API to authorize your application. 

Multiple redirect URIs can be entered in the Redirect_URI field. Each entry should be separated by a space or newline.

A `Redirect_URI` follows this format:

    URLprotocol://[sub-domain.]domain_name[:port]/path

#### URL Protocol

Three URL protocols are supported, depending on the purpose: - `http:// protocol` - `https:// protocol` - `custom_url:// protocol`

***`http:// protocol`***

(Works in: Sandbox only)

The `http://` format is only accepted in the sandbox environment. It is typically used by developers for local testing by using `http://localhost/` however, any domain name can be used.  

***`https://protocol`***

(Works in: Sandbox \| Production)

The `https://` format is used for secure communication and is required for all applications in the production environment unless the application is using the Mobile OAuth method for handling callbacks.

***`custom_url:// protocol`***

(Works in: Sandbox \| Production)

The `custom_url` protocol is used by mobile applications to handle communications directly with your application on a mobile device.

If you are using Mobile OAuth support for communication directly with a mobile device the `custom_url` should follow this format:

    Top-level.domain(TLD).domain-name[.sub-domain][.app_name]

For example, if the Blue Button 2.0 API team created an application we might create a custom_url of:

    gov.cms.bluebutton.oauthtester

This would then be incorporated into a redirect URI entry. Here is an example:

    gov.cms.bluebutton.oauthtester:8080//bluebutton_app/callback.html

### Web Application Flow

To use this flow your application should be registered with `Client Type` set to `confidential` and `Grant Type` set to `authorization-code`.

#### Request authorization from user

To allow a user to authorize your application, direct them to the Blue Button 2.0 API `authorize` endpoint. The request must include the `response_type` set to `code`, your application's client_id, and your application's redirect_uri. An optional `state` field that your application can use to identify the authorization request is recommended.

    https://sandbox.bluebutton.cms.gov/v1/o/authorize/?client_id=swBu7LWsCnIRfu530qnfPw1y5vMmER3lAM2L6rq2
        &redirect_uri=http://localhost:8080/testclient/callback
        &response_type=code
        &state=8e896a59f0744a8e93bf2f1f13230be5

#### Exchange `code` for `token`

After visiting the authorization page a user will be redirected back to the `redirect_uri` registered with your application.

For example if the `redirect_uri` is `http://localhost:8080/testclient/callback` BlueButton will redirect with this request.

    GET http://localhost:8080/testclient/callback?code=TSjqiZCdJwGyytGjz2GzziPfHTJ6z2
        &state=8e896a59f0744a8e93bf2f1f13230be5

Your application can now exchange the code provided in the redirected request for a full `token`. Send a `POST` request to the BlueButton `token` endpoint providing the `code`, the application's `client_id`, `client_secret`, and `redirect_uri`. Your request must also specify the `grant_type` which should always be `authorization_code` for this flow.

    curl -X POST "https://sandbox.bluebutton.cms.gov/v1/o/token/" \
        -u "swBu7LWsCnIRfu530qnfPw1y5vMmER3lAM2L6rq2:<client_secret>" \
        -d "code=TSjqiZCdJwGyytGjz2GzziPfHTJ6z2
        &grant_type=authorization_code
        &redirect_uri=http://localhost/testclient/callback"

Response

    {
        "access_token": "oQlduHNr09GKCU506GOgp8OarrAy2q",
        "expires_in": 16768.523842,
        "token_type": "Bearer",
        "scope": "profile patient/Patient.read patient/ExplanationOfBenefit.read patient/Coverage.read"
        "refresh_token": "wDimPGoA8vwXP51kie71vpsy9l17HN"
    }

### Client Application Flow

To use this flow your application should be registered with `Client Type` set to `public` and `Grant Type` set to `implicit`.

#### Request authorization from user

To use the client application flow direct the user to the Blue Button 2.0 API `authorization` endpoint with the `response_type` parameter set to `token`.

    https://sandbox.bluebutton.cms.gov/v1/o/authorize/?client_id=swBu7LWsCnIRfu530qnfPw1y5vMmER3lAM2L6rq2
        &redirect_uri=http://localhost:8080/testclient/callback
        &response_type=token
        &state=8e896a59f0744a8e93bf2f1f13230be5

If the user authorizes your application they will be redirected back to the `redirect_uri` of your application. The request will include an `access_token` in the fragment.

    http://localhost:8080/testclient/callback#access_token=KCHMTX5VHNAXYGYv38eG2RLAX4hL6R
        &expires_in=35849.875807
        &token_type=Bearer
        &scope=profile+patient%2FPatient.read+patient%2FExplanationOfBenefit.read+patient%2FCoverage.read
        &state=8e896a59f0744a8e93bf2f1f13230be5

Below you will find a sample account you can use to test your Blue Button 2.0 API OAuth implementation. This account mimics a valid Medicare account but has reduced functionality. For example, you cannot test “Forgot Password” flow.

*Jane Doe Username: BBUser29999 Password: PW29999!*

------------------------------------------------------------------------

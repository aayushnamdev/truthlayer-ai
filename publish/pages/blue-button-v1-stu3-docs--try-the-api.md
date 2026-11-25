---
id: "blue-button-v1-stu3-docs--try-the-api"
title: "Try the API"
api_version: "2 (FHIR R4)"
verified_on: 2026-11-25
source:
  file: "docs/v1/blue-button-v1-stu3-docs.md"
  sha256: "30976f71442d0b15c92ef5e77a151b40e64d74fbf7fb41ad93793b299fa37f69"
  lines: "34-179"
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
## Try the API

To join the Developer Sandbox, register a sample application and retrieve synthetic data for a sample Patient ID by calling the API, follow these four steps:

**Step 1:** [Join the Developer Sandbox](https://sandbox.bluebutton.cms.gov/v1/accounts/create) and register a sample application

Click "Add an Application" to register a new sample application and get a Client ID and Secret

**Step 2:** Generate a sample token

To test out the Blue Button API, you must first generate a sample token that represents a beneficiary granting consent.

To see a sample of Blue Button data you can access the Test Client.

1.  If you are already logged in to the Developer portal, log out
2.  In the navigation bar on <https://sandbox.bluebutton.cms.gov> click on "Test Client"
3.  Click "sample Authorization flow"
4.  Click the Authorization Link to authorize
5.  You will be redirected to your Medicare account. Login with one of the synthetic beneficiary accounts

<div class="ds-c-alert ds-c-alert--hide-icon ds-u-margin-bottom--2">

<div class="ds-c-alert__body">

<h3 class="ds-c-alert__heading">
Synthetic Beneficiary Accounts
</h3>
<p class="ds-c-alert__text">
The first user is <strong>BBUser00000</strong> with password <strong>PW00000!</strong> and these sample users continue all the way to <strong>BBUser29999</strong> with password <strong>PW29999!</strong> <i>Note: the ! at the end of the password is required</i>
</p>

</div>

</div>

6.  Click "Allow" to Authorize sharing
7.  Review the details returned from the Authorization flow
8.  Make some API calls for the beneficiary account you used to authorize access

**Step 3:** Call the API

Try this out in Postman:

1.  From the Postman app, open a new tab

2.  Paste the Request URL: `https://sandbox.bluebutton.cms.gov/v1/fhir/Patient/-20140000008325`

3.  Click "Authorization" and select type "OAuth 2.0"

4.  Click on "Get New Access Token"

5.  Enter the following parameters:

    **Token Name:** {The name of your app}

    **Grant Type:** Authorization Code (unless you have chosen an alternate value for your app)

    **Callback URL:** One of the redirect uris you registered for your app, for example:

        http://localhost:3000

    **Auth URL:**

        https://sandbox.bluebutton.cms.gov/v1/o/authorize/

    **Access Token URL:**

        https://sandbox.bluebutton.cms.gov/v1/o/token/

    **Client ID:** {The Client ID assigned to your App in the sandbox}

    **Client Secret:** {The Client Secret assigned to your App in the sandbox}

    **Scope:**

        patient/Patient.read patient/Coverage.read patient/ExplanationOfBenefit.read profile

    *NOTE:* When a beneficiary is authorizing your application, they will have the ability to omit the `patient/Patient.read` scope. **Be sure that you build your application accordingly to handle a 403 error if a beneficiary decides to filter their demographic information.**

    **State:** An optional value that you may use in your app

    **Client Authentication:** Select "Send as Basic Auth header"

6.  Click Request Token. You should see a pop up for your Medicare account. Login using one of the synthetic beneficiary accounts

<div class="ds-c-alert ds-c-alert--hide-icon ds-u-margin-bottom--2">

<div class="ds-c-alert__body">

<h3 class="ds-c-alert__heading">
Synthetic Beneficiary Accounts
</h3>
<p class="ds-c-alert__text">

The first user is <strong>BBUser00000</strong> with password <strong>PW00000!</strong> and these sample users continue all the way to <strong>BBUser29999</strong> with password <strong>PW29999!</strong>

<i>Note: the ! at the end of the password is required</i>
</p>

</div>

</div>

7.  Authorize sharing by clicking "Allow" on the authorization screen
8.  When you return to the Postman workspace you should now be able to make requests to the API using the Bearer Token that will have been placed in the Header
9.  Click "Send" and see the synthetic beneficiary's personal health information as a Patient FHIR Resource display under "Body" in Postman

Once you have the Bearer Token you can also use Curl to make queries as follows:

<pre>
curl --header "Authorization: Bearer YOUR TOKEN HERE" https://sandbox.bluebutton.cms.gov/v1/fhir/Patient/-20140000008325
</pre>

**Step 4:** View the API Response

In the API response for Patient -20140000008325 you will find: - 32 total claims (140 total claim lines) - 25 carrier claims (110 carrier claim lines) - 2 inpatient claims (25 inpatient claim lines) - 5 Part D events

**Step 5:** Accessing Synthetic Data In order to access the full synthetic dataset for an individual synthetic beneficiary, you can do the following: 1. Set up your sandbox application 2. Log out of <https://sandbox.bluebutton.cms.gov>. 3. Access the authorization url at <https://sandbox.bluebutton.cms.gov/v1/o/authorize/>

    *Note: The last backslash is important*.
    *Also remember to append ?client_id={your client_id assigned to the application you registered}*

4.  You will be redirected to the Medicare authentication screen on. DO NOT ACCESS THIS PAGE DIRECTLY.
5.  Use one of thirty thousand provided usernames and passwords.

<div class="ds-c-alert ds-c-alert--hide-icon ds-u-margin-bottom--2">

<div class="ds-c-alert__body">

<h3 class="ds-c-alert__heading">
Synthetic Beneficiary Accounts
</h3>
<p class="ds-c-alert__text">
The first user is <strong>BBUser00000</strong> with password <strong>PW00000!</strong> and these sample users continue all the way to <strong>BBUser29999</strong> with password <strong>PW29999!</strong> <i>Note: the ! at the end of the password is required</i>
</p>

</div>

</div>

6.  Approve access for your application, which will now receive an access token, which can be used in the requests described above.

7.  The authorization completes when you are redirected back to the Redirect_URI you specified when you registered your application.

------------------------------------------------------------------------

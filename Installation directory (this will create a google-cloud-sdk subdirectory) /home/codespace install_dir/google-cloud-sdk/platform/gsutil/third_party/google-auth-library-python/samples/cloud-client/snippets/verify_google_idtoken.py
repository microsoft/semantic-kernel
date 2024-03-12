# Copyright 2022 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START auth_cloud_verify_google_idtoken]

import google
import google.auth.transport.requests
from google.oauth2 import id_token


def verify_google_idtoken(idtoken: str, audience="iap.googleapis.com",
                          jwk_url="https://www.googleapis.com/oauth2/v3/certs"):
    """
      Verifies the obtained Google id token. This is done at the receiving end of the OIDC endpoint.
      The most common use case for verifying the ID token is when you are protecting
      your own APIs with IAP. Google services already verify credentials as a platform,
      so verifying ID tokens before making Google API calls is usually unnecessary.

    Args:
        idtoken: The Google ID token to verify.

        audience: The service name for which the id token is requested. Service name refers to the
            logical identifier of an API service, such as "iap.googleapis.com".

        jwk_url: To verify id tokens, get the Json Web Key endpoint (jwk).
            OpenID Connect allows the use of a "Discovery document," a JSON document found at a
            well-known location containing key-value pairs which provide details about the
            OpenID Connect provider's configuration.
            For more information on validating the jwt, see:
            https://developers.google.com/identity/protocols/oauth2/openid-connect#validatinganidtoken

            Here, we validate Google's token using Google's OpenID Connect service (jwkUrl).
            For more information on jwk,see:
            https://auth0.com/docs/secure/tokens/json-web-tokens/json-web-key-sets
    """

    request = google.auth.transport.requests.Request()
    # Set the parameters and verify the token.
    # Setting "certs_url" is optional. When verifying a Google ID token, this is set by default.
    result = id_token.verify_token(idtoken, request, audience, clock_skew_in_seconds=10)

    # Verify that the token contains subject and email claims.
    # Get the User id.
    if not result["sub"] is None:
        print(f"User id: {result['sub']}")
    # Optionally, if "INCLUDE_EMAIL" was set in the token options, check if the
    # email was verified.
    if result['email_verified'] == "True":
        print(f"Email verified {result['email']}")

# [END auth_cloud_verify_google_idtoken]

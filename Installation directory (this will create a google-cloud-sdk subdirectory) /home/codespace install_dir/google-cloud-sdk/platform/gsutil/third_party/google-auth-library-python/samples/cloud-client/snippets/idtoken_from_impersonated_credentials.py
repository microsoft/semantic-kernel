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

# [auth_cloud_idtoken_impersonated_credentials]

import google
from google.auth import impersonated_credentials
import google.auth.transport.requests


def idtoken_from_impersonated_credentials(
        impersonated_service_account: str, scope: str, target_audience: str):
    """
      Use a service account (SA1) to impersonate as another service account (SA2) and obtain id token
      for the impersonated account.
      To obtain token for SA2, SA1 should have the "roles/iam.serviceAccountTokenCreator" permission
      on SA2.

    Args:
        impersonated_service_account: The name of the privilege-bearing service account for whom the credential is created.
            Examples: name@project.service.gserviceaccount.com

        scope: Provide the scopes that you might need to request to access Google APIs,
            depending on the level of access you need.
            For this example, we use the cloud-wide scope and use IAM to narrow the permissions.
            https://cloud.google.com/docs/authentication#authorization_for_services
            For more information, see: https://developers.google.com/identity/protocols/oauth2/scopes

        target_audience: The service name for which the id token is requested. Service name refers to the
            logical identifier of an API service, such as "iap.googleapis.com".
            Examples: iap.googleapis.com
    """

    # Construct the GoogleCredentials object which obtains the default configuration from your
    # working environment.
    credentials, project_id = google.auth.default()

    # Create the impersonated credential.
    target_credentials = impersonated_credentials.Credentials(
        source_credentials=credentials,
        target_principal=impersonated_service_account,
        # delegates: The chained list of delegates required to grant the final accessToken.
        # For more information, see:
        # https://cloud.google.com/iam/docs/create-short-lived-credentials-direct#sa-credentials-permissions
        # Delegate is NOT USED here.
        delegates=[],
        target_scopes=[scope],
        lifetime=300)

    # Set the impersonated credential, target audience and token options.
    id_creds = impersonated_credentials.IDTokenCredentials(
        target_credentials,
        target_audience=target_audience,
        include_email=True)

    # Get the ID token.
    # Once you've obtained the ID token, use it to make an authenticated call
    # to the target audience.
    request = google.auth.transport.requests.Request()
    id_creds.refresh(request)
    # token = id_creds.token
    print("Generated ID token.")

# [auth_cloud_idtoken_impersonated_credentials]

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

# [START auth_cloud_idtoken_metadata_server]

import google
import google.oauth2.credentials
from google.auth import compute_engine
import google.auth.transport.requests


def idtoken_from_metadata_server(url: str):
    """
    Use the Google Cloud metadata server in the Cloud Run (or AppEngine or Kubernetes etc.,)
    environment to create an identity token and add it to the HTTP request as part of an
    Authorization header.

    Args:
        url: The url or target audience to obtain the ID token for.
            Examples: http://www.abc.com
    """

    request = google.auth.transport.requests.Request()
    # Set the target audience.
    # Setting "use_metadata_identity_endpoint" to "True" will make the request use the default application
    # credentials. Optionally, you can also specify a specific service account to use by mentioning
    # the service_account_email.
    credentials = compute_engine.IDTokenCredentials(
        request=request, target_audience=url, use_metadata_identity_endpoint=True
    )

    # Get the ID token.
    # Once you've obtained the ID token, use it to make an authenticated call
    # to the target audience.
    credentials.refresh(request)
    # print(credentials.token)
    print("Generated ID token.")

# [END auth_cloud_idtoken_metadata_server]

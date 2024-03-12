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

# [START auth_cloud_idtoken_service_account]

import google.auth
import google.auth.transport.requests

from google.oauth2 import service_account


def get_idToken_from_serviceaccount(json_credential_path: str, target_audience: str):
    """
    TODO(Developer): Replace the below variables before running the code.

    *NOTE*:
    Using service account keys introduces risk; they are long-lived, and can be used by anyone
    that obtains the key. Proper rotation and storage reduce this risk but do not eliminate it.
    For these reasons, you should consider an alternative approach that
    does not use a service account key. Several alternatives to service account keys
    are described here:
    https://cloud.google.com/docs/authentication/external/set-up-adc

    Args:
        json_credential_path: Path to the service account json credential file.
        target_audience: The url or target audience to obtain the ID token for.
                        Examples: http://www.abc.com
    """

    # Obtain the id token by providing the json file path and target audience.
    credentials = service_account.IDTokenCredentials.from_service_account_file(
        filename=json_credential_path,
        target_audience=target_audience)

    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    print("Generated ID token.")

# [END auth_cloud_idtoken_service_account]

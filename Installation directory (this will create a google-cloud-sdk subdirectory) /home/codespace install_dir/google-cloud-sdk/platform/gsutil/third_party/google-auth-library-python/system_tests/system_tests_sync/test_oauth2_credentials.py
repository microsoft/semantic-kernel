# Copyright 2016 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from google.auth import _helpers
import google.oauth2.credentials

GOOGLE_OAUTH2_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


def test_refresh(authorized_user_file, http_request, token_info):
    with open(authorized_user_file, "r") as fh:
        info = json.load(fh)

    credentials = google.oauth2.credentials.Credentials(
        None,  # No access token, must be refreshed.
        refresh_token=info["refresh_token"],
        token_uri=GOOGLE_OAUTH2_TOKEN_ENDPOINT,
        client_id=info["client_id"],
        client_secret=info["client_secret"],
    )

    credentials.refresh(http_request)

    assert credentials.token

    info = token_info(credentials.token)

    info_scopes = _helpers.string_to_scopes(info["scope"])

    # Canonical list of scopes at https://cloud.google.com/sdk/gcloud/reference/auth/application-default/login
    # or do `gcloud auth application-defaut login --help`
    canonical_scopes = set(
        [
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/cloud-platform",
            "openid",
        ]
    )
    # When running the test locally, we always have an additional "accounts.reauth" scope.
    canonical_scopes_with_reauth = canonical_scopes.copy()
    canonical_scopes_with_reauth.add("https://www.googleapis.com/auth/accounts.reauth")
    assert set(info_scopes) == canonical_scopes or set(info_scopes) == canonical_scopes_with_reauth

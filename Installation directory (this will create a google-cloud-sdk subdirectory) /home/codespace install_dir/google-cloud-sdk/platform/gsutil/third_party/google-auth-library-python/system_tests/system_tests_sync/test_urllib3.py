# Copyright 2021 Google LLC
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

import google.auth
import google.auth.credentials
import google.auth.transport.requests
from google.oauth2 import service_account


def test_authorized_session_with_service_account_and_self_signed_jwt():
    credentials, project_id = google.auth.default()

    credentials = credentials.with_scopes(
        scopes=[],
        default_scopes=["https://www.googleapis.com/auth/pubsub"],
    )

    http = google.auth.transport.urllib3.AuthorizedHttp(
        credentials=credentials, default_host="pubsub.googleapis.com"
    )

    # List Pub/Sub Topics through the REST API
    # https://cloud.google.com/pubsub/docs/reference/rest/v1/projects.topics/list
    response = http.urlopen(
        method="GET",
        url="https://pubsub.googleapis.com/v1/projects/{}/topics".format(project_id)
    )

    assert response.status == 200

    # Check that self-signed JWT was created and is being used
    assert credentials._jwt_credentials is not None
    assert credentials._jwt_credentials.token == credentials.token

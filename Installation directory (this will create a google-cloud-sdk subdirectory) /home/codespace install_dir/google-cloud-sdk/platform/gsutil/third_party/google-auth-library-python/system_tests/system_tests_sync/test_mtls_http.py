# Copyright 2020 Google LLC
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
import mock
import os
import time
from os import path


import google.auth
import google.auth.credentials
from google.auth import environment_vars
from google.auth.transport import mtls
import google.auth.transport.requests
import google.auth.transport.urllib3

MTLS_ENDPOINT = "https://pubsub.mtls.googleapis.com/v1/projects/{}/topics"
REGULAR_ENDPOINT = "https://pubsub.googleapis.com/v1/projects/{}/topics"


def test_requests():
    credentials, project_id = google.auth.default()
    credentials = google.auth.credentials.with_scopes_if_required(
        credentials, ["https://www.googleapis.com/auth/pubsub"]
    )

    authed_session = google.auth.transport.requests.AuthorizedSession(credentials)
    with mock.patch.dict(os.environ, {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"}):
        authed_session.configure_mtls_channel()

    # If the devices has default client cert source, then a mutual TLS channel
    # is supposed to be created.
    assert authed_session.is_mtls == mtls.has_default_client_cert_source()

    # Sleep 1 second to avoid 503 error.
    time.sleep(1)

    if authed_session.is_mtls:
        response = authed_session.get(MTLS_ENDPOINT.format(project_id))
    else:
        response = authed_session.get(REGULAR_ENDPOINT.format(project_id))

    assert response.ok


def test_urllib3():
    credentials, project_id = google.auth.default()
    credentials = google.auth.credentials.with_scopes_if_required(
        credentials, ["https://www.googleapis.com/auth/pubsub"]
    )

    authed_http = google.auth.transport.urllib3.AuthorizedHttp(credentials)
    with mock.patch.dict(os.environ, {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"}):
        is_mtls = authed_http.configure_mtls_channel()

    # If the devices has default client cert source, then a mutual TLS channel
    # is supposed to be created.
    assert is_mtls == mtls.has_default_client_cert_source()

    # Sleep 1 second to avoid 503 error.
    time.sleep(1)

    if is_mtls:
        response = authed_http.request("GET", MTLS_ENDPOINT.format(project_id))
    else:
        response = authed_http.request("GET", REGULAR_ENDPOINT.format(project_id))

    assert response.status == 200


def test_requests_with_default_client_cert_source():
    credentials, project_id = google.auth.default()
    credentials = google.auth.credentials.with_scopes_if_required(
        credentials, ["https://www.googleapis.com/auth/pubsub"]
    )

    authed_session = google.auth.transport.requests.AuthorizedSession(credentials)

    if mtls.has_default_client_cert_source():
        with mock.patch.dict(os.environ, {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"}):
            authed_session.configure_mtls_channel(
                client_cert_callback=mtls.default_client_cert_source()
            )

        assert authed_session.is_mtls

        # Sleep 1 second to avoid 503 error.
        time.sleep(1)

        response = authed_session.get(MTLS_ENDPOINT.format(project_id))
        assert response.ok


def test_urllib3_with_default_client_cert_source():
    credentials, project_id = google.auth.default()
    credentials = google.auth.credentials.with_scopes_if_required(
        credentials, ["https://www.googleapis.com/auth/pubsub"]
    )

    authed_http = google.auth.transport.urllib3.AuthorizedHttp(credentials)

    if mtls.has_default_client_cert_source():
        with mock.patch.dict(os.environ, {environment_vars.GOOGLE_API_USE_CLIENT_CERTIFICATE: "true"}):
            assert authed_http.configure_mtls_channel(
                client_cert_callback=mtls.default_client_cert_source()
            )

        # Sleep 1 second to avoid 503 error.
        time.sleep(1)

        response = authed_http.request("GET", MTLS_ENDPOINT.format(project_id))
        assert response.status == 200

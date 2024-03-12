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
import pytest

import google.oauth2.credentials
from google.oauth2 import service_account
import google.auth.impersonated_credentials
from google.auth import _helpers


GOOGLE_OAUTH2_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


@pytest.fixture
def service_account_credentials(service_account_file):
    yield service_account.Credentials.from_service_account_file(service_account_file)


@pytest.fixture
def impersonated_service_account_credentials(impersonated_service_account_file):
    yield service_account.Credentials.from_service_account_file(
        impersonated_service_account_file
    )


def test_refresh_with_user_credentials_as_source(
    authorized_user_file,
    impersonated_service_account_credentials,
    http_request,
    token_info,
):
    with open(authorized_user_file, "r") as fh:
        info = json.load(fh)

    source_credentials = google.oauth2.credentials.Credentials(
        None,
        refresh_token=info["refresh_token"],
        token_uri=GOOGLE_OAUTH2_TOKEN_ENDPOINT,
        client_id=info["client_id"],
        client_secret=info["client_secret"],
        # The source credential needs this scope for the generateAccessToken request
        # The user must also have `Service Account Token Creator` on the project
        # that owns the impersonated service account.
        # See https://cloud.google.com/iam/docs/creating-short-lived-service-account-credentials
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )

    source_credentials.refresh(http_request)

    target_scopes = [
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/analytics",
    ]
    target_credentials = google.auth.impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=impersonated_service_account_credentials.service_account_email,
        target_scopes=target_scopes,
        lifetime=100,
    )

    target_credentials.refresh(http_request)
    assert target_credentials.token


def test_refresh_with_service_account_credentials_as_source(
    http_request,
    service_account_credentials,
    impersonated_service_account_credentials,
    token_info,
):
    source_credentials = service_account_credentials.with_scopes(["email"])
    source_credentials.refresh(http_request)
    assert source_credentials.token

    target_scopes = [
        "https://www.googleapis.com/auth/devstorage.read_only",
        "https://www.googleapis.com/auth/analytics",
    ]
    target_credentials = google.auth.impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=impersonated_service_account_credentials.service_account_email,
        target_scopes=target_scopes,
    )

    target_credentials.refresh(http_request)
    assert target_credentials.token

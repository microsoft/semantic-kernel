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
import os

from google.auth import _helpers
import google.auth.transport.requests
import google.auth.transport.urllib3
import pytest
import requests
import urllib3


HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, "../data")
IMPERSONATED_SERVICE_ACCOUNT_FILE = os.path.join(
    DATA_DIR, "impersonated_service_account.json"
)
SERVICE_ACCOUNT_FILE = os.path.join(DATA_DIR, "service_account.json")
URLLIB3_HTTP = urllib3.PoolManager(retries=False)
REQUESTS_SESSION = requests.Session()
REQUESTS_SESSION.verify = False
TOKEN_INFO_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"


@pytest.fixture
def service_account_file():
    """The full path to a valid service account key file."""
    yield SERVICE_ACCOUNT_FILE


@pytest.fixture
def impersonated_service_account_file():
    """The full path to a valid service account key file."""
    yield IMPERSONATED_SERVICE_ACCOUNT_FILE


@pytest.fixture
def authorized_user_file():
    """The full path to a valid authorized user file."""
    yield AUTHORIZED_USER_FILE


@pytest.fixture(params=["urllib3", "requests"])
def request_type(request):
    yield request.param


@pytest.fixture
def http_request(request_type):
    """A transport.request object."""
    if request_type == "urllib3":
        yield google.auth.transport.urllib3.Request(URLLIB3_HTTP)
    elif request_type == "requests":
        yield google.auth.transport.requests.Request(REQUESTS_SESSION)


@pytest.fixture
def authenticated_request(request_type):
    """A transport.request object that takes credentials"""
    if request_type == "urllib3":

        def wrapper(credentials):
            return google.auth.transport.urllib3.AuthorizedHttp(
                credentials, http=URLLIB3_HTTP
            ).request

        yield wrapper
    elif request_type == "requests":

        def wrapper(credentials):
            session = google.auth.transport.requests.AuthorizedSession(credentials)
            session.verify = False
            return google.auth.transport.requests.Request(session)

        yield wrapper


@pytest.fixture
def token_info(http_request):
    """Returns a function that obtains OAuth2 token info."""

    def _token_info(access_token=None, id_token=None):
        query_params = {}

        if access_token is not None:
            query_params["access_token"] = access_token
        elif id_token is not None:
            query_params["id_token"] = id_token
        else:
            raise ValueError("No token specified.")

        url = _helpers.update_query(TOKEN_INFO_URL, query_params)

        response = http_request(url=url, method="GET")

        return json.loads(response.data.decode("utf-8"))

    yield _token_info


@pytest.fixture
def verify_refresh(http_request):
    """Returns a function that verifies that credentials can be refreshed."""

    def _verify_refresh(credentials):
        if credentials.requires_scopes:
            credentials = credentials.with_scopes(["email", "profile"])

        credentials.refresh(http_request)

        assert credentials.token
        assert credentials.valid

    yield _verify_refresh


def verify_environment():
    """Checks to make sure that requisite data files are available."""
    if not os.path.isdir(DATA_DIR):
        raise EnvironmentError(
            "In order to run system tests, test data must exist in "
            "system_tests/data. See CONTRIBUTING.rst for details."
        )


def pytest_configure(config):
    """Pytest hook that runs before Pytest collects any tests."""
    verify_environment()

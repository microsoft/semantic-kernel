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
import os

from google.auth import _helpers
import google.auth.transport.requests
import google.auth.transport.urllib3
import pytest
import pytest_asyncio
import requests
import urllib3

import aiohttp
from google.auth.transport import _aiohttp_requests as aiohttp_requests
from system_tests.system_tests_sync import conftest as sync_conftest


TOKEN_INFO_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"


@pytest_asyncio.fixture
def service_account_file():
    """The full path to a valid service account key file."""
    yield sync_conftest.SERVICE_ACCOUNT_FILE


@pytest_asyncio.fixture
def impersonated_service_account_file():
    """The full path to a valid service account key file."""
    yield sync_conftest.IMPERSONATED_SERVICE_ACCOUNT_FILE


@pytest_asyncio.fixture
def authorized_user_file():
    """The full path to a valid authorized user file."""
    yield sync_conftest.AUTHORIZED_USER_FILE


@pytest_asyncio.fixture
async def aiohttp_session():
    async with aiohttp.ClientSession(auto_decompress=False) as session:
        yield session


@pytest_asyncio.fixture(params=["aiohttp"])
async def http_request(request, aiohttp_session):
    """A transport.request object."""
    yield aiohttp_requests.Request(aiohttp_session)


@pytest_asyncio.fixture
async def token_info(http_request):
    """Returns a function that obtains OAuth2 token info."""

    async def _token_info(access_token=None, id_token=None):
        query_params = {}

        if access_token is not None:
            query_params["access_token"] = access_token
        elif id_token is not None:
            query_params["id_token"] = id_token
        else:
            raise ValueError("No token specified.")

        url = _helpers.update_query(sync_conftest.TOKEN_INFO_URL, query_params)

        response = await http_request(url=url, method="GET")

        data = await response.content()

        return json.loads(data.decode("utf-8"))

    yield _token_info


@pytest_asyncio.fixture
async def verify_refresh(http_request):
    """Returns a function that verifies that credentials can be refreshed."""

    async def _verify_refresh(credentials):
        if credentials.requires_scopes:
            credentials = credentials.with_scopes(["email", "profile"])

        await credentials.refresh(http_request)

        assert credentials.token
        assert credentials.valid

    yield _verify_refresh


def verify_environment():
    """Checks to make sure that requisite data files are available."""
    if not os.path.isdir(sync_conftest.DATA_DIR):
        raise EnvironmentError(
            "In order to run system tests, test data must exist in "
            "system_tests/data. See CONTRIBUTING.rst for details."
        )


def pytest_configure(config):
    """Pytest hook that runs before Pytest collects any tests."""
    verify_environment()

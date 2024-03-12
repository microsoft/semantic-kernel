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

import pytest

from google.auth import _helpers
from google.auth import exceptions
from google.auth import iam
from google.oauth2 import _service_account_async


@pytest.fixture
def credentials(service_account_file):
    yield _service_account_async.Credentials.from_service_account_file(service_account_file)


@pytest.mark.asyncio
async def test_refresh_no_scopes(http_request, credentials):
    """
    We expect the http request to refresh credentials
    without scopes provided to throw an error.
    """
    with pytest.raises(exceptions.RefreshError):
        await credentials.refresh(http_request)

@pytest.mark.asyncio
async def test_refresh_success(http_request, credentials, token_info):
    credentials = credentials.with_scopes(["email", "profile"])
    await credentials.refresh(http_request)

    assert credentials.token

    info = await token_info(credentials.token)

    assert info["email"] == credentials.service_account_email
    info_scopes = _helpers.string_to_scopes(info["scope"])
    assert set(info_scopes) == set(
        [
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ]
    )
